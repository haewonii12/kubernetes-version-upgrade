"""ClusterInspectorTool — Kubernetes 클러스터 Read-Only 조회를 감싼 AgentTool (Section 4)."""

from __future__ import annotations

import anyio

from app.agent.tools.base import AgentTool, ToolContext
from app.collectors.assemble import collect_full_cluster_info
from app.collectors.node import detect_node_inconsistencies
from app.models.agent import Task, ToolCapability, ToolResult


class ClusterInspectorTool(AgentTool):
    name = "cluster_inspector"
    description = (
        "Kubernetes 클러스터의 버전/노드/컨트롤플레인/etcd/CNI/CSI/CRD/설치된 소프트웨어를 "
        "Read-Only(get/list)로 수집한다."
    )
    capabilities = [ToolCapability.CLUSTER_READ]

    async def execute(self, task: Task, ctx: ToolContext) -> ToolResult:
        assert ctx.mcp_client is not None, "ClusterInspectorTool은 mcp_client가 필요합니다"
        cluster = await anyio.to_thread.run_sync(collect_full_cluster_info, ctx.mcp_client)
        node_warnings = detect_node_inconsistencies(cluster.nodes)

        ctx.state.memory_working["cluster"] = cluster.model_dump(mode="json")
        ctx.state.memory_working["node_warnings"] = node_warnings
        ctx.state.cluster_current_version = cluster.kubernetes_version

        return ToolResult(
            tool_name=self.name,
            ok=True,
            data={"cluster": cluster.model_dump(mode="json"), "node_warnings": node_warnings},
            summary=(
                f"Kubernetes {cluster.kubernetes_version}, 노드 {len(cluster.nodes)}대, "
                f"CNI={cluster.cni}, 설치된 소프트웨어 {len(cluster.software_inventory)}종 확인"
                + (f", 노드 불일치 {len(node_warnings)}건" if node_warnings else "")
            ),
        )
