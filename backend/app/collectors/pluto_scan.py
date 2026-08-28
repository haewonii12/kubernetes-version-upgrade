"""pluto(FairwindsOps/pluto) 교차검증 (Section 11 하이브리드).

RAG 판정과 별개로, 이 저장소가 관리하지 않는 넓은 deprecated/removed API
데이터셋(pluto 바이너리에 내장)으로 한 번 더 훑는다. 폐쇄망 대응: pluto는
단일 Go 바이너리에 ``versions.yaml`` 을 ``go:embed`` 하므로 인터넷이 필요 없다
(Docker 이미지 빌드 시점에 구워넣음 — docker/backend/Dockerfile).

``pluto detect-files`` 를 쓴다 — 클러스터 접근 없이 매니페스트 파일만 스캔하므로
Read-Only RBAC 제약과도 무관하다. 입력 매니페스트는 ``manifest_scan`` 이 이미
모아 둔 라이브 오브젝트 + Helm 차트 매니페스트다.
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

import yaml

from app.core.config import settings
from app.models.upgrade import DeprecatedAPIFinding, DeprecatedAPIStatus

logger = logging.getLogger(__name__)

_TIMEOUT_SECONDS = 30


def pluto_available() -> bool:
    return shutil.which(settings.pluto_command) is not None


def scan_with_pluto(gathered: list[dict], target_version: str) -> tuple[list[DeprecatedAPIFinding], str | None]:
    """(findings, skip_reason). pluto가 없거나 실패하면 ([], 사유)."""
    if not pluto_available():
        return [], f"pluto 바이너리({settings.pluto_command})를 찾을 수 없어 교차검증을 건너뜁니다."
    if not gathered:
        return [], None

    target_minor = ".".join(target_version.lstrip("v").split(".")[:2])
    with tempfile.TemporaryDirectory(prefix="pluto-scan-") as tmp:
        d = Path(tmp)
        for i, g in enumerate(gathered):
            (d / f"{i:04d}.yaml").write_text(yaml.safe_dump(g["obj"]), encoding="utf-8")
        origin_by_index = {f"{i:04d}.yaml": g["found_in"] for i, g in enumerate(gathered)}

        try:
            proc = subprocess.run(
                [
                    settings.pluto_command, "detect-files",
                    "-d", str(d),
                    "-o", "json",
                    "--target-versions", f"k8s=v{target_minor}.0",
                ],
                capture_output=True, text=True, timeout=_TIMEOUT_SECONDS,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            return [], f"pluto 실행 실패: {exc}"

        # pluto는 탐지 항목이 있으면 exit code 3(=deprecated)/2(=removed)로 끝난다. stdout(JSON)만 본다.
        raw = proc.stdout.strip()
        if not raw:
            return [], None
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return [], f"pluto 출력 파싱 실패: {raw[:200]}"

    findings: list[DeprecatedAPIFinding] = []
    for item in data.get("items") or []:
        api = item.get("api", {})
        removed = bool(item.get("removed"))
        deprecated = bool(item.get("deprecated"))
        if not (removed or deprecated):
            continue
        fname = Path(item.get("filePath", "")).name
        found_in = origin_by_index.get(fname, "live")
        status = DeprecatedAPIStatus.UPGRADE_BLOCKER if removed else DeprecatedAPIStatus.ACTION_REQUIRED
        if status == DeprecatedAPIStatus.UPGRADE_BLOCKER and found_in.startswith("helm"):
            status = DeprecatedAPIStatus.ACTION_REQUIRED
        findings.append(
            DeprecatedAPIFinding(
                resource_kind=api.get("kind") or item.get("kind") or "?",
                api_version=api.get("version") or "?",
                resource_name=item.get("name"),
                namespace=item.get("namespace") or None,
                deprecated_in_version=_strip_v(api.get("deprecated-in")),
                removed_in_version=_strip_v(api.get("removed-in")),
                replacement_api_version=api.get("replacement-api") or None,
                status=status,
                evaluated_at_target_version=target_minor,
                sources=[],
                scanned_by="pluto",
                found_in=found_in,
                notes="pluto 내장 데이터셋 기준.",
            )
        )
    return findings, None


def _strip_v(v: str | None) -> str | None:
    if not v:
        return None
    v = v.lstrip("v")
    parts = v.split(".")
    return f"{parts[0]}.{parts[1]}" if len(parts) >= 2 else v
