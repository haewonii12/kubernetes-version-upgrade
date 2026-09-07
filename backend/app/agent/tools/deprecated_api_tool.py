"""DeprecatedApiTool — agents/deprecated_api.py + collectors/pluto_scan.py 를 그대로 감싼 AgentTool."""

from __future__ import annotations

import anyio

from app.agent.tools.base import AgentTool, ToolContext
from app.agents.deprecated_api import evaluate_deprecated_apis, merge_findings, summarize_deprecated_apis
from app.agents.planner import compute_upgrade_path
from app.collectors.manifest_scan import gather_manifest_objects, to_observed
from app.collectors.pluto_scan import scan_with_pluto
from app.models.agent import Evidence, Task, ToolCapability, ToolResult


def _minor_label(version: str) -> str:
    parts = version.split(".")
    return f"{parts[0]}.{parts[1]}"


class DeprecatedApiTool(AgentTool):
    name = "deprecated_api_checker"
    description = (
        "라이브 오브젝트 + 미적용 Helm 차트 매니페스트에서 Deprecated/Removed API 사용 현황을 "
        "RAG 근거 + pluto 교차검증으로 판정한다."
    )
    capabilities = [ToolCapability.DEPRECATED_API]

    async def execute(self, task: Task, ctx: ToolContext) -> ToolResult:
        assert ctx.rag is not None and ctx.mcp_client is not None

        target_version = task.input.get("target_version") or (ctx.state.goal.target_version if ctx.state.goal else None)
        upgrade_path = task.input.get("upgrade_path")
        if upgrade_path is None and target_version and ctx.state.cluster_current_version:
            upgrade_path = compute_upgrade_path(ctx.state.cluster_current_version, target_version)
        if not upgrade_path:
            return ToolResult(
                tool_name=self.name,
                ok=False,
                summary="목표 버전을 알 수 없어 Deprecated API 검사를 수행할 수 없습니다.",
                error="missing_target_version",
            )

        gathered = await anyio.to_thread.run_sync(gather_manifest_objects, ctx.mcp_client)
        rag_findings = evaluate_deprecated_apis(to_observed(gathered), upgrade_path, ctx.rag)
        target_minor = _minor_label(upgrade_path[-1])
        pluto_findings, pluto_skip_reason = await anyio.to_thread.run_sync(scan_with_pluto, gathered, target_minor)
        findings = merge_findings(rag_findings, pluto_findings)
        summary_findings = summarize_deprecated_apis(findings)

        evidence = [Evidence.from_rag_reference(ref) for f in findings for ref in f.sources]
        ctx.state.memory_working.setdefault("deprecated_findings", [])
        ctx.state.memory_working["deprecated_findings"].extend(f.model_dump(mode="json") for f in findings)

        blockers = sum(1 for f in findings if f.status.value in ("ACTION_REQUIRED", "UPGRADE_BLOCKER", "UNKNOWN"))
        summary = f"Deprecated/Removed API {len(findings)}건 검사 완료 (조치 필요 {blockers}건)"
        if pluto_skip_reason:
            summary += f" — pluto 교차검증 생략: {pluto_skip_reason}"

        return ToolResult(
            tool_name=self.name,
            ok=True,
            data={
                "findings": [f.model_dump(mode="json") for f in findings],
                "summary": [f.model_dump(mode="json") for f in summary_findings],
                "pluto_skip_reason": pluto_skip_reason,
            },
            summary=summary,
            evidence=evidence,
        )
