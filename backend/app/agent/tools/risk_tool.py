"""RiskAnalyzerTool — agents/risk.py 를 그대로 감싼 AgentTool.

이 Tool은 외부 I/O가 전혀 없다 — cluster_inspector/compatibility_checker/
deprecated_api_checker가 WorkingMemory(``ctx.state.memory_working``)에 남긴
결과를 조합만 한다. 전제 조건 데이터가 없으면 실패로 처리하지 않고 ok=False로
반환해 Observer가 ``requires_further_investigation`` 을 세우도록 한다.
"""

from __future__ import annotations

from app.agent.tools.base import AgentTool, ToolContext
from app.agents.risk import build_risk_findings
from app.models.agent import Task, ToolCapability, ToolResult
from app.models.compatibility import CompatibilityResult
from app.models.risk import ReadinessScore
from app.models.upgrade import DeprecatedAPIFinding


class RiskAnalyzerTool(AgentTool):
    name = "risk_analyzer"
    description = "클러스터 상태 + Compatibility + Deprecated API 결과를 종합해 Risk와 Readiness Score를 산정한다."
    capabilities = [ToolCapability.RISK]

    async def execute(self, task: Task, ctx: ToolContext) -> ToolResult:
        cluster_dump = ctx.state.memory_working.get("cluster")
        if cluster_dump is None:
            return ToolResult(
                tool_name=self.name,
                ok=False,
                summary="cluster_inspector 결과가 없어 Risk를 계산할 수 없습니다.",
                error="missing_cluster",
            )

        from app.models.cluster import ClusterInfo

        cluster = ClusterInfo.model_validate(cluster_dump)
        node_warnings = ctx.state.memory_working.get("node_warnings", [])
        compatibility_results = [
            CompatibilityResult.model_validate(r) for r in ctx.state.memory_working.get("compatibility_results", [])
        ]
        deprecated_findings = [
            DeprecatedAPIFinding.model_validate(f) for f in ctx.state.memory_working.get("deprecated_findings", [])
        ]

        risks = build_risk_findings(cluster, node_warnings, compatibility_results, deprecated_findings)
        readiness = ReadinessScore.from_findings(risks)
        ctx.state.memory_working["risks"] = [r.model_dump(mode="json") for r in risks]
        ctx.state.memory_working["readiness"] = readiness.model_dump(mode="json")

        return ToolResult(
            tool_name=self.name,
            ok=True,
            data={"risks": [r.model_dump(mode="json") for r in risks], "readiness": readiness.model_dump(mode="json")},
            summary=(
                f"Risk {len(risks)}건 (BLOCKER {readiness.blocker_count}, HIGH {readiness.high_count}), "
                f"업그레이드 준비 복잡도 {readiness.complexity}%"
            ),
        )
