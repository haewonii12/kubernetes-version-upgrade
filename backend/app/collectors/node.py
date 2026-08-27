"""Node별 OS/Kernel/cgroup/Container Runtime 수집 (Section 13)."""

from __future__ import annotations

import re

from app.collectors._utils import is_control_plane_node
from app.mcp.client import MCPClient
from app.models.cluster import NodeInfo, NodeRole

_CONSISTENCY_FIELDS = [
    "os_name",
    "os_version",
    "kernel_version",
    "cgroup_version",
    "container_runtime",
    "container_runtime_version",
]


def parse_os_image(os_image: str) -> tuple[str | None, str | None]:
    if not os_image:
        return None, None
    if m := re.match(r"Red Hat Enterprise Linux\s+(\d+(?:\.\d+)?)", os_image):
        return "RHEL", m.group(1)
    if m := re.match(r"Ubuntu\s+(\d+\.\d+(?:\.\d+)?)", os_image):
        return "Ubuntu", m.group(1)
    if m := re.match(r"([A-Za-z ]+?)\s+(\d+[\d.]*)", os_image):
        return m.group(1).strip(), m.group(2)
    return os_image, None


def parse_container_runtime(runtime_version: str) -> tuple[str | None, str | None]:
    if not runtime_version or "://" not in runtime_version:
        return None, None
    name, _, version = runtime_version.partition("://")
    return name, version


def infer_cgroup_version_hint(os_name: str | None, os_version: str | None) -> str | None:
    """OS 기본값 기반 best-effort 추정치.

    실제 cgroup 버전은 커널/호스트 마운트 상태에 달려 있어 get/list/watch 만으로는
    확정할 수 없다 (Section 30의 Read-Only RBAC 제약). 정확한 값은 각 노드에서
    ``stat -fc %T /sys/fs/cgroup`` 실행 결과(cgroup2fs=v2, tmpfs=v1)로 반드시 재검증해야
    하며, 이 함수의 반환값은 Upgrade Report에 "추정치"로 표기된다.
    """
    if not os_name or not os_version:
        return None
    try:
        major = int(os_version.split(".")[0])
    except ValueError:
        return None
    if os_name == "RHEL":
        return "v2" if major >= 9 else "v1"
    if os_name == "Ubuntu":
        return "v2" if major >= 22 else "v1"
    return None


class NodeCollector:
    def __init__(self, client: MCPClient) -> None:
        self._client = client

    def collect(self) -> list[NodeInfo]:
        nodes: list[NodeInfo] = []
        for raw in self._client.get_nodes():
            info = raw.get("status", {}).get("nodeInfo", {})
            os_name, os_version = parse_os_image(info.get("osImage", ""))
            runtime, runtime_version = parse_container_runtime(info.get("containerRuntimeVersion", ""))
            role = NodeRole.CONTROL_PLANE if is_control_plane_node(raw) else NodeRole.WORKER
            ready = any(
                c.get("type") == "Ready" and c.get("status") == "True"
                for c in raw.get("status", {}).get("conditions", [])
            )
            kubelet_version = (info.get("kubeletVersion") or "").lstrip("v") or None
            nodes.append(
                NodeInfo(
                    name=raw["metadata"]["name"],
                    role=role,
                    os_name=os_name,
                    os_version=os_version,
                    kernel_version=info.get("kernelVersion"),
                    architecture=info.get("architecture"),
                    cgroup_version=infer_cgroup_version_hint(os_name, os_version),
                    container_runtime=runtime,
                    container_runtime_version=runtime_version,
                    kubelet_version=kubelet_version,
                    ready=ready,
                )
            )
        return nodes


def detect_node_inconsistencies(nodes: list[NodeInfo]) -> list[str]:
    """Node 간 값이 다르면 경고 문자열 목록을 반환한다 (Section 13)."""
    warnings: list[str] = []
    for field in _CONSISTENCY_FIELDS:
        values = {getattr(n, field) for n in nodes if getattr(n, field) is not None}
        if len(values) > 1:
            warnings.append(f"Node 간 {field} 값이 서로 다릅니다: {sorted(values)}")
    return warnings
