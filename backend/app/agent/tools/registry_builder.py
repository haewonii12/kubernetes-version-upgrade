"""build_default_registry — 모든 구체 Tool을 아는 유일한 composition root.

``app.agent.executor``/``app.agent.runtime`` 은 이 함수가 반환한 ``ToolRegistry`` 만
받는다 — 어떤 구체 Tool 클래스가 있는지 orchestration 코드는 전혀 모른다. 새 Tool을
추가할 때 건드릴 곳은 이 파일 하나뿐이다.
"""

from __future__ import annotations

from app.agent.tools import ToolRegistry
from app.agent.tools.cluster_tools import ClusterInspectorTool
from app.agent.tools.compatibility_tool import CompatibilityCheckerTool
from app.agent.tools.deprecated_api_tool import DeprecatedApiTool
from app.agent.tools.github_tool import GitHubTool
from app.agent.tools.k8s_docs_tool import OfficialKubernetesDocsTool
from app.agent.tools.observability_stubs import ArgoCDTool, GitTool, GrafanaTool, PrometheusTool
from app.agent.tools.rag_tool import InternalRagTool
from app.agent.tools.risk_tool import RiskAnalyzerTool
from app.agent.tools.web_search_tool import WebSearchTool
from app.core.config import Settings


def build_default_registry(*, settings: Settings) -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(ClusterInspectorTool())
    registry.register(CompatibilityCheckerTool())
    registry.register(DeprecatedApiTool())
    registry.register(RiskAnalyzerTool())
    registry.register(InternalRagTool())
    registry.register(
        WebSearchTool(api_key=settings.agent_web_search_api_key, endpoint=settings.agent_web_search_endpoint)
    )
    registry.register(OfficialKubernetesDocsTool(enabled=settings.agent_open_network_enabled))
    registry.register(GitHubTool(enabled=settings.agent_open_network_enabled, token=settings.agent_github_token))
    registry.register(PrometheusTool(endpoint=settings.agent_prometheus_endpoint))
    registry.register(GrafanaTool(endpoint=settings.agent_grafana_endpoint))
    registry.register(ArgoCDTool(endpoint=settings.agent_argocd_endpoint))
    registry.register(GitTool())
    return registry
