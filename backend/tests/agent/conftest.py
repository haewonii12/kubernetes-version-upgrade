from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.agent.state import AgentState
from app.agent.tools import ToolRegistry, ToolRetriever
from app.agent.tools.base import ToolContext
from app.agent.tools.registry_builder import build_default_registry
from app.core.config import Settings
from app.models.agent import Goal


@pytest.fixture
def open_network_disabled_settings() -> Settings:
    """오픈 네트워크 Tool이 전부 not_configured로 fallback하도록 강제한 설정.

    실제 API 키/인터넷 연결 없이도 결정론적으로 테스트가 통과해야 하기 때문.
    """
    return Settings(agent_open_network_enabled=False, agent_web_search_api_key=None, agent_github_token=None)


@pytest.fixture
def agent_registry(open_network_disabled_settings: Settings) -> ToolRegistry:
    return build_default_registry(settings=open_network_disabled_settings)


@pytest.fixture
def tool_retriever(agent_registry: ToolRegistry) -> ToolRetriever:
    return ToolRetriever(agent_registry)


@pytest.fixture
def agent_state_factory():
    def _make(*, goal_text: str, target_version: str | None = None, success_criteria: list[str] | None = None) -> AgentState:
        state = AgentState(run_id="test-run")
        state.set_goal(
            Goal(
                goal=goal_text,
                target_version=target_version,
                success_criteria=success_criteria or [],
                created_at=datetime.now(UTC),
            )
        )
        return state

    return _make


@pytest.fixture
def tool_context_factory(mock_mcp_client, rag_retriever, open_network_disabled_settings):
    def _make(state: AgentState, *, llm_client=None) -> ToolContext:
        return ToolContext(
            state=state,
            mcp_client=mock_mcp_client,
            rag=rag_retriever,
            llm_client=llm_client,
            settings=open_network_disabled_settings,
        )

    return _make
