"""6-노드 LangGraph 전체를 mock 모드로 한 번 돌려서 노드 구성과 종료를 확인한다."""

from __future__ import annotations

import pytest

from app.agent.runtime import build_agent_runtime
from app.agent.state import AgentState, AgentStatus


@pytest.mark.asyncio
async def test_full_graph_run_visits_all_six_nodes_and_terminates(
    mock_mcp_client, rag_retriever, agent_registry, open_network_disabled_settings
):
    runtime = build_agent_runtime(
        mcp_client=mock_mcp_client, rag=rag_retriever, llm_client=None, registry=agent_registry, settings=open_network_disabled_settings
    )
    graph = runtime.build_graph(lambda ev: None)
    state = AgentState(run_id="graph-test", raw_request="현재 클러스터 상태만 분석해줘")

    visited: list[str] = []
    async for step in graph.astream({"agent_state": state}, stream_mode="updates"):
        visited.extend(step.keys())

    for expected in ("goal_manager", "planner", "executor", "observer", "critic", "finalizer"):
        assert expected in visited

    assert state.status == AgentStatus.COMPLETED
    assert state.final_conclusion is not None
    assert state.final_conclusion.goal_met is True


@pytest.mark.asyncio
async def test_mutating_tool_is_never_executed(agent_state_factory, tool_context_factory, agent_registry):
    """Section 8 Safety: is_mutating=True인 Tool은 Executor가 절대 execute()를 호출하지 않는다."""
    from unittest.mock import AsyncMock

    from app.agent.executor import Executor
    from app.agent.tools.base import AgentTool
    from app.models.agent import Task, TaskStatus, ToolCapability, ToolResult

    class DummyMutatingTool(AgentTool):
        name = "dummy_mutating"
        description = "test"
        capabilities: list[ToolCapability] = []
        is_mutating = True
        execute = AsyncMock(return_value=ToolResult(tool_name="dummy_mutating", ok=True, summary="should not run"))

    agent_registry.register(DummyMutatingTool())
    state = agent_state_factory(goal_text="delete something")
    ctx = tool_context_factory(state)
    executor = Executor(agent_registry)

    task = Task(id="t1", description="delete node", tool_name="dummy_mutating")
    state.add_task(task)
    results = await executor.execute_batch([task], ctx, lambda *_: None)

    DummyMutatingTool.execute.assert_not_called()
    assert results == []
    assert task.status == TaskStatus.SKIPPED
    assert len(state.memory_working.get("proposed_actions", [])) == 1
