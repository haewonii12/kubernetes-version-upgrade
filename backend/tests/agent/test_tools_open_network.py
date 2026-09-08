"""Open Network Tool: API 키/설정이 없으면 절대 실제 호출을 시도하지 않고 not_configured로 fallback."""

from __future__ import annotations

import pytest

from app.agent.tools.base import ToolContext
from app.agent.tools.github_tool import GitHubTool
from app.agent.tools.k8s_docs_tool import OfficialKubernetesDocsTool
from app.agent.tools.web_search_tool import WebSearchTool
from app.models.agent import Task


@pytest.mark.asyncio
async def test_web_search_without_api_key_never_calls_network(agent_state_factory, tool_context_factory, httpx_mock):
    state = agent_state_factory(goal_text="search")
    ctx = tool_context_factory(state)
    tool = WebSearchTool(api_key=None, endpoint="https://api.tavily.com/search")

    result = await tool.execute(Task(id="1", description="search calico"), ctx)

    assert result.not_configured is True
    assert result.ok is False
    assert httpx_mock.get_requests() == []


@pytest.mark.asyncio
async def test_web_search_with_api_key_calls_endpoint(agent_state_factory, tool_context_factory, httpx_mock):
    httpx_mock.add_response(
        url="https://api.tavily.com/search",
        method="POST",
        json={"results": [{"title": "Calico compatibility", "url": "https://example.com", "content": "..."}]},
    )
    state = agent_state_factory(goal_text="search")
    ctx = tool_context_factory(state)
    tool = WebSearchTool(api_key="fake-key", endpoint="https://api.tavily.com/search")

    result = await tool.execute(Task(id="1", description="x", input={"query": "calico 3.30.7 kubernetes 1.37"}), ctx)

    assert result.ok is True
    assert len(result.evidence) == 1
    assert result.evidence[0].source_type == "web_search"


@pytest.mark.asyncio
async def test_github_tool_disabled_by_default(agent_state_factory, tool_context_factory, httpx_mock):
    state = agent_state_factory(goal_text="search")
    ctx = tool_context_factory(state)
    tool = GitHubTool(enabled=False)

    result = await tool.execute(Task(id="1", description="search"), ctx)

    assert result.not_configured is True
    assert httpx_mock.get_requests() == []


@pytest.mark.asyncio
async def test_official_docs_tool_disabled_by_default(agent_state_factory, tool_context_factory, httpx_mock):
    state = agent_state_factory(goal_text="docs")
    ctx = tool_context_factory(state)
    tool = OfficialKubernetesDocsTool(enabled=False)

    result = await tool.execute(Task(id="1", description="docs", input={"url": "https://kubernetes.io/docs/x"}), ctx)

    assert result.not_configured is True
    assert httpx_mock.get_requests() == []


@pytest.mark.asyncio
async def test_official_docs_tool_rejects_non_allowlisted_domain(agent_state_factory, tool_context_factory, httpx_mock):
    state = agent_state_factory(goal_text="docs")
    ctx = tool_context_factory(state)
    tool = OfficialKubernetesDocsTool(enabled=True)

    result = await tool.execute(Task(id="1", description="docs", input={"url": "https://evil.example.com/x"}), ctx)

    assert result.ok is False
    assert "허용되지 않은 도메인" in (result.error or "") or "허용되지 않은 도메인" in result.summary
