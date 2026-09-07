"""Test Scenario 6: max_iterations에 도달하면 무한 loop 없이 종료하고
부족한 evidence를 명확히 표시해야 한다.
"""

from __future__ import annotations

import pytest

from app.agent.runtime import build_agent_runtime
from app.agent.state import AgentState, AgentStatus


@pytest.mark.asyncio
async def test_max_iterations_forces_clean_finish(mock_mcp_client, rag_retriever, agent_registry, open_network_disabled_settings):
    runtime = build_agent_runtime(
        mcp_client=mock_mcp_client, rag=rag_retriever, llm_client=None, registry=agent_registry, settings=open_network_disabled_settings
    )
    graph = runtime.build_graph(lambda ev: None)

    # 업그레이드 평가 목표는 4개 Task가 있고 mock 데이터에는 대개 미해결 항목이
    # 남아 critic이 계속 insufficient를 반환한다 — max_iterations=1로 강제해
    # replan 없이 즉시 종료되는지 확인한다.
    state = AgentState(
        run_id="guardrail-test",
        raw_request="1.32에서 1.36으로 업그레이드 가능한지 분석해줘",
        goal_target_version_hint="1.36",
        max_iterations=1,
    )

    result = await graph.ainvoke({"agent_state": state})
    final_state: AgentState = result["agent_state"]

    assert final_state.status == AgentStatus.MAX_ITERATIONS_REACHED
    assert final_state.final_conclusion is not None
    assert final_state.final_conclusion.stopped_reason == "max_iterations"
    assert final_state.final_conclusion.goal_met is False
    # 무한 루프 없이 정확히 1 iteration만 진행되고 끝났어야 한다.
    assert final_state.iteration == 1


@pytest.mark.asyncio
async def test_max_tool_calls_stops_mid_batch_cleanly(mock_mcp_client, rag_retriever, agent_registry, open_network_disabled_settings):
    runtime = build_agent_runtime(
        mcp_client=mock_mcp_client, rag=rag_retriever, llm_client=None, registry=agent_registry, settings=open_network_disabled_settings
    )
    graph = runtime.build_graph(lambda ev: None)

    state = AgentState(
        run_id="toolcall-guardrail-test",
        raw_request="1.32에서 1.36으로 업그레이드 가능한지 분석해줘",
        goal_target_version_hint="1.36",
        max_tool_calls=2,
    )

    result = await graph.ainvoke({"agent_state": state})
    final_state: AgentState = result["agent_state"]

    assert len(final_state.tool_calls) == 2
    assert final_state.final_conclusion is not None
    assert final_state.final_conclusion.stopped_reason == "max_tool_calls"
    # 실행되지 못한 나머지 Task는 RUNNING으로 방치되지 않고 SKIPPED로 정리되어야 한다.
    from app.models.agent import TaskStatus

    assert all(t.status != TaskStatus.RUNNING for t in final_state.plan)
