"""Compatibility 판단 (Section 8, 25).

이 모듈은 "어떤 컴포넌트가 어떤 버전과 호환되는지"를 전혀 모른다 — 오직
``RAGRetriever.lookup_compatibility`` 가 rag/documents 의 구조화된
``compatibility_matrix`` 블록에서 찾아준 결과를 그대로 전달할 뿐이다.
근거가 없으면 항상 UNKNOWN이 되며 이 모듈이 임의로 COMPATIBLE/INCOMPATIBLE을
추측하지 않는다.
"""

from __future__ import annotations

from app.models.cluster import ClusterInfo
from app.models.compatibility import CompatibilityResult, CompatibilityStatus
from app.rag.retriever import RAGRetriever

_STATUS_ORDER = {
    CompatibilityStatus.COMPATIBLE: 0,
    CompatibilityStatus.UNKNOWN: 1,
    CompatibilityStatus.WARNING: 2,
    CompatibilityStatus.INCOMPATIBLE: 3,
}


def slugify_component(name: str) -> str:
    return name.strip().lower().replace(" ", "-")


def gather_components(cluster: ClusterInfo) -> list[tuple[str, str | None]]:
    """Compatibility 검사 대상 (component_slug, current_version) 목록.

    Namespace Software Inventory + Node 레벨(OS/Kernel/cgroup/Container Runtime).
    Node 간 값이 다르면 이미 별도 Risk(node-consistency)로 보고되므로, 여기서는
    첫 번째 Node 값을 대표값으로 사용한다.
    """
    components: dict[str, str | None] = {}
    for sw in cluster.software_inventory:
        components.setdefault(slugify_component(sw.name), sw.version)

    if cluster.nodes:
        primary = cluster.nodes[0]
        if primary.container_runtime:
            components.setdefault(slugify_component(primary.container_runtime), primary.container_runtime_version)
        if primary.os_name:
            components.setdefault(slugify_component(primary.os_name), primary.os_version)
        if primary.kernel_version:
            components.setdefault("kernel", primary.kernel_version)
        if primary.cgroup_version:
            components.setdefault("cgroup", primary.cgroup_version)
    return list(components.items())


def evaluate_compatibility(
    cluster: ClusterInfo, upgrade_path: list[str], rag: RAGRetriever
) -> list[CompatibilityResult]:
    target_minors = _target_minors(upgrade_path)
    results: list[CompatibilityResult] = []
    for component, version in gather_components(cluster):
        for minor in target_minors:
            results.append(rag.lookup_compatibility(component, version, minor))
    return results


def summarize_compatibility(results: list[CompatibilityResult]) -> list[CompatibilityResult]:
    """Section 21 Installed Software UI 등 Global 테이블용 — 컴포넌트당 가장 나쁜(이른) 상태 하나로 압축."""
    best: dict[str, CompatibilityResult] = {}
    for r in results:
        current = best.get(r.component)
        if current is None or _STATUS_ORDER[r.status] > _STATUS_ORDER[current.status]:
            best[r.component] = r
    return list(best.values())


def _target_minors(upgrade_path: list[str]) -> list[str]:
    minors = [_minor_label(v) for v in upgrade_path[1:]]
    return minors or [_minor_label(v) for v in upgrade_path]


def _minor_label(version: str) -> str:
    parts = version.split(".")
    return f"{parts[0]}.{parts[1]}"
