"""Deprecated / Removed API 검사 (Section 11, 25).

라이브 오브젝트 + 미적용 Helm 차트 매니페스트에서 모은 (kind, apiVersion) 쌍을
RAG의 Deprecated/Removed API Guide와 대조한다. 근거가 없는 조합은:
  - stable(GA, beta/alpha 아님) → 조용히 OK (노이즈 억제)
  - beta/alpha → UNKNOWN (Manual Verification Required)
로 처리하고, 임의로 BLOCKER를 추측하지 않는다.

pluto 교차검증 결과는 ``collectors/pluto_scan`` 이 별도로 만들고
``upgrade_agent`` 에서 병합한다.
"""

from __future__ import annotations

from app.models.rag import RAGReference
from app.models.upgrade import DeprecatedAPIFinding, DeprecatedAPIStatus
from app.rag.retriever import RAGRetriever

_STATUS_ORDER = {
    DeprecatedAPIStatus.OK: 0,
    DeprecatedAPIStatus.UNKNOWN: 1,
    DeprecatedAPIStatus.ACTION_REQUIRED: 2,
    DeprecatedAPIStatus.UPGRADE_BLOCKER: 3,
}


def _minor_tuple(v: str) -> tuple[int, int]:
    major, minor = v.lstrip("v").split(".")[:2]
    return int(major), int(minor)


def _minor_label(version: str) -> str:
    parts = version.split(".")
    return f"{parts[0]}.{parts[1]}"


def _is_prerelease(api_version: str) -> bool:
    v = api_version.lower()
    return "beta" in v or "alpha" in v


def evaluate_deprecated_apis(
    observed: list[dict], upgrade_path: list[str], rag: RAGRetriever
) -> list[DeprecatedAPIFinding]:
    target_minors = [_minor_label(v) for v in upgrade_path[1:]] or [_minor_label(v) for v in upgrade_path]
    findings: list[DeprecatedAPIFinding] = []

    for obs in observed:
        kind, api_version = obs["kind"], obs.get("api_version")
        if not api_version:
            continue
        found_in = obs.get("found_in", "live")
        entry = rag.lookup_deprecated_api(kind, api_version)

        if entry is None:
            if not _is_prerelease(api_version):
                continue  # GA로 보이는데 근거 없음 → 조용히 OK
            findings.append(
                DeprecatedAPIFinding(
                    resource_kind=kind,
                    api_version=api_version,
                    resource_name=obs.get("name"),
                    namespace=obs.get("namespace"),
                    status=DeprecatedAPIStatus.UNKNOWN,
                    evaluated_at_target_version=target_minors[0],
                    sources=[],
                    scanned_by="rag",
                    found_in=found_in,
                    notes="beta/alpha API인데 RAG 문서에 판정 근거가 없습니다.",
                )
            )
            continue

        removed_in = entry.get("removed_in_version")
        deprecated_in = entry.get("deprecated_in_version")
        source = RAGReference(document=entry["document_title"], section="deprecated_api_guide", doc_id=entry["doc_id"])

        for minor in target_minors:
            status = DeprecatedAPIStatus.OK
            if removed_in and _minor_tuple(minor) >= _minor_tuple(removed_in):
                status = DeprecatedAPIStatus.UPGRADE_BLOCKER
            elif deprecated_in and _minor_tuple(minor) >= _minor_tuple(deprecated_in):
                status = DeprecatedAPIStatus.ACTION_REQUIRED
            # 라이브가 아닌 Helm 매니페스트에서만 발견된, 이미 제거된 API는 지금 당장
            # 클러스터를 막지는 않으므로(다음 helm upgrade 때 깨짐) 한 단계 낮춰 보고한다.
            if status == DeprecatedAPIStatus.UPGRADE_BLOCKER and found_in.startswith("helm"):
                status = DeprecatedAPIStatus.ACTION_REQUIRED
            if status == DeprecatedAPIStatus.OK:
                continue
            findings.append(
                DeprecatedAPIFinding(
                    resource_kind=kind,
                    api_version=api_version,
                    resource_name=obs.get("name"),
                    namespace=obs.get("namespace"),
                    deprecated_in_version=deprecated_in,
                    removed_in_version=removed_in,
                    replacement_api_version=entry.get("replacement_api_version"),
                    status=status,
                    evaluated_at_target_version=minor,
                    sources=[source],
                    scanned_by="rag",
                    found_in=found_in,
                    notes=(entry.get("notes") or "").strip() or None,
                )
            )
    return findings


def merge_findings(*groups: list[DeprecatedAPIFinding]) -> list[DeprecatedAPIFinding]:
    """RAG + pluto 결과 병합. 같은 (kind, apiVersion, name, ns, target)면 더 심각한 것 하나만 남기되,
    RAG 판정(근거 링크 있음)을 우선한다."""
    best: dict[tuple, DeprecatedAPIFinding] = {}
    for group in groups:
        for f in group:
            key = (f.resource_kind, f.api_version, f.resource_name, f.namespace, f.evaluated_at_target_version)
            cur = best.get(key)
            if cur is None:
                best[key] = f
                continue
            if _STATUS_ORDER[f.status] > _STATUS_ORDER[cur.status]:
                best[key] = f
            elif _STATUS_ORDER[f.status] == _STATUS_ORDER[cur.status] and cur.scanned_by != "rag" and f.scanned_by == "rag":
                best[key] = f
    return list(best.values())


def summarize_deprecated_apis(findings: list[DeprecatedAPIFinding]) -> list[DeprecatedAPIFinding]:
    """Section 11/20 Global 테이블용 — 리소스당 가장 이르고 심각한 상태 하나로 압축."""
    best: dict[tuple[str, str, str | None, str | None], DeprecatedAPIFinding] = {}
    for f in findings:
        key = (f.resource_kind, f.api_version, f.resource_name, f.namespace)
        current = best.get(key)
        if current is None or _STATUS_ORDER[f.status] > _STATUS_ORDER[current.status]:
            best[key] = f
    return list(best.values())
