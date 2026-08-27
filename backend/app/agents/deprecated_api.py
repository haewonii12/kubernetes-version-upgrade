"""Deprecated / Removed API 검사 (Section 11, 25).

실제 Cluster에 존재하는 Resource의 apiVersion을 RAG의 Deprecated/Removed API
Guide와 대조한다. 근거가 없는 조합은 UNKNOWN으로 남기고 임의로 BLOCKER를
추측하지 않는다.
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
    major, minor = v.split(".")[:2]
    return int(major), int(minor)


def _minor_label(version: str) -> str:
    parts = version.split(".")
    return f"{parts[0]}.{parts[1]}"


def evaluate_deprecated_apis(
    observed: list[dict], upgrade_path: list[str], rag: RAGRetriever
) -> list[DeprecatedAPIFinding]:
    target_minors = [_minor_label(v) for v in upgrade_path[1:]] or [_minor_label(v) for v in upgrade_path]
    findings: list[DeprecatedAPIFinding] = []

    for obs in observed:
        kind, api_version = obs["kind"], obs.get("api_version")
        if not api_version:
            continue
        entry = rag.lookup_deprecated_api(kind, api_version)

        if entry is None:
            findings.append(
                DeprecatedAPIFinding(
                    resource_kind=kind,
                    api_version=api_version,
                    resource_name=obs.get("name"),
                    namespace=obs.get("namespace"),
                    status=DeprecatedAPIStatus.UNKNOWN,
                    evaluated_at_target_version=target_minors[0],
                    sources=[],
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
                )
            )
    return findings


def summarize_deprecated_apis(findings: list[DeprecatedAPIFinding]) -> list[DeprecatedAPIFinding]:
    """Section 11/20 Global 테이블용 — 리소스당 가장 이르고 심각한 상태 하나로 압축."""
    best: dict[tuple[str, str, str | None, str | None], DeprecatedAPIFinding] = {}
    for f in findings:
        key = (f.resource_kind, f.api_version, f.resource_name, f.namespace)
        current = best.get(key)
        if current is None or _STATUS_ORDER[f.status] > _STATUS_ORDER[current.status]:
            best[key] = f
    return list(best.values())
