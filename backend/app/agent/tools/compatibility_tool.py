"""CompatibilityCheckerTool — agents/compatibility.py 를 그대로 감싼 AgentTool.

판정 로직은 전혀 재구현하지 않는다 (Section 4 DRY 요구사항). ``task.input`` 에
``component``/``component_version`` 이 있으면 특정 컴포넌트 하나만 재확인하는
"scoped delta check" 로 동작한다 — Observer가 mid-run에 발견한 컴포넌트(예: Calico)를
Planner가 재확인 Task로 만들 때 이 경로를 탄다.
"""

from __future__ import annotations

from app.agent.tools.base import AgentTool, ToolContext
from app.agents.compatibility import evaluate_compatibility, summarize_compatibility
from app.agents.planner import compute_upgrade_path
from app.models.agent import Evidence, Task, ToolCapability, ToolResult
from app.models.cluster import ClusterInfo


def _minor_label(version: str) -> str:
    parts = version.split(".")
    return f"{parts[0]}.{parts[1]}"


def _target_minors(upgrade_path: list[str]) -> list[str]:
    minors = [_minor_label(v) for v in upgrade_path[1:]]
    return minors or [_minor_label(v) for v in upgrade_path]


class CompatibilityCheckerTool(AgentTool):
    name = "compatibility_checker"
    description = (
        "설치된 컴포넌트(CNI/CSI/Container Runtime/OS 등)와 목표 Kubernetes 버전 간 "
        "Compatibility를 RAG 근거(rag/documents/compatibility-matrix)로 판정한다."
    )
    capabilities = [ToolCapability.COMPATIBILITY]

    async def execute(self, task: Task, ctx: ToolContext) -> ToolResult:
        assert ctx.rag is not None, "CompatibilityCheckerTool은 rag가 필요합니다"
        cluster_dump = ctx.state.memory_working.get("cluster")
        if cluster_dump is None:
            return ToolResult(
                tool_name=self.name,
                ok=False,
                summary="cluster_inspector 결과가 없어 Compatibility를 계산할 수 없습니다.",
                error="missing_cluster",
            )

        target_version = task.input.get("target_version") or (ctx.state.goal.target_version if ctx.state.goal else None)
        upgrade_path = task.input.get("upgrade_path")
        if upgrade_path is None and target_version and ctx.state.cluster_current_version:
            upgrade_path = compute_upgrade_path(ctx.state.cluster_current_version, target_version)

        component = task.input.get("component")
        if component and upgrade_path:
            version = task.input.get("component_version")
            results = [ctx.rag.lookup_compatibility(component, version, minor) for minor in _target_minors(upgrade_path)]
        elif upgrade_path:
            cluster = ClusterInfo.model_validate(cluster_dump)
            results = evaluate_compatibility(cluster, upgrade_path, ctx.rag)
        else:
            return ToolResult(
                tool_name=self.name,
                ok=False,
                summary="목표 버전을 알 수 없어 Compatibility를 계산할 수 없습니다.",
                error="missing_target_version",
            )

        summary_results = summarize_compatibility(results)
        evidence = [Evidence.from_rag_reference(ref) for res in results for ref in res.sources]
        ctx.state.memory_working.setdefault("compatibility_results", [])
        ctx.state.memory_working["compatibility_results"].extend(r.model_dump(mode="json") for r in results)

        attention = sum(1 for r in results if r.status.value != "COMPATIBLE")
        return ToolResult(
            tool_name=self.name,
            ok=True,
            data={
                "results": [r.model_dump(mode="json") for r in results],
                "summary": [r.model_dump(mode="json") for r in summary_results],
            },
            summary=f"Compatibility {len(results)}건 판정 완료 (주의 필요 {attention}건)",
            evidence=evidence,
        )
