"""Prometheus/Grafana/ArgoCD/Git — 이번 pass에서는 등록만 되고 항상 not_configured인 스텁.

ToolRetriever가 이들을 discover할 수 있음을 보여주기 위해 등록하지만("Tool 추가는
orchestration 코드를 안 건드린다"), 실제 fetch 로직은 분석/계획 생성 범위를
벗어나므로 구현하지 않는다 (Section 8 scope cut).
"""

from __future__ import annotations

from app.agent.tools.base import ToolContext
from app.agent.tools.open_network_base import OpenNetworkTool
from app.models.agent import Task, ToolCapability, ToolResult


class _AlwaysStubTool(OpenNetworkTool):
    def __init__(self, *, endpoint: str | None = None, timeout: float = 10.0) -> None:
        super().__init__(enabled=False, timeout=timeout)
        self._endpoint = endpoint

    async def execute(self, task: Task, ctx: ToolContext) -> ToolResult:
        return self._not_configured_result()


class PrometheusTool(_AlwaysStubTool):
    name = "prometheus"
    description = "Prometheus 메트릭 조회 (이번 pass 범위 밖 — 스텁)."
    capabilities = [ToolCapability.OBSERVABILITY]


class GrafanaTool(_AlwaysStubTool):
    name = "grafana"
    description = "Grafana 대시보드 조회 (이번 pass 범위 밖 — 스텁)."
    capabilities = [ToolCapability.OBSERVABILITY]


class ArgoCDTool(_AlwaysStubTool):
    name = "argocd"
    description = "ArgoCD Application 동기화 상태 조회 (이번 pass 범위 밖 — 스텁)."
    capabilities = [ToolCapability.GITOPS]


class GitTool(_AlwaysStubTool):
    name = "git"
    description = "Git 저장소 이력 조회 (이번 pass 범위 밖 — 스텁)."
    capabilities = [ToolCapability.SOURCE_CODE]
