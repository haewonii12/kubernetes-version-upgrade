"""Test Scenario 4: 증거 부족 -> insufficient -> replan.
Test Scenario 5: 증거 충분 -> 불필요한 추가 Tool 호출 없이 종료.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.agent.critic import Critic
from app.agent.executor import Executor
from app.agent.observer import Observer
from app.agent.planner import Planner
from app.models.agent import Task, TaskStatus, ToolCallRecord


def test_insufficient_evidence_triggers_replan_signal(agent_state_factory):
    """success_criteria를 뒷받침할 성공한 Tool 호출이 하나도 없으면 Critic은 insufficient를 반환해야 한다."""
    state = agent_state_factory(
        goal_text="클러스터 상태 분석",
        success_criteria=["현재 클러스터 상태를 사실 기반으로 파악한다"],
    )
    critic = Critic(llm_client=None)
    verdict = critic.judge(state)

    assert verdict.sufficient is False
    assert verdict.missing_evidence  # 비어있지 않아야 함


async def test_sufficient_evidence_finishes_without_extra_calls(
    agent_state_factory, agent_registry, tool_retriever, tool_context_factory
):
    """narrow goal(Scenario 1)이 cluster_inspector 한 번만 실행하고도 충분 판정을 받아야 한다."""
    state = agent_state_factory(
        goal_text="현재 클러스터 상태만 분석해줘",
        success_criteria=["클러스터의 현재 버전/노드/설정 상태를 사실 기반으로 파악한다"],
    )
    planner = Planner(tool_retriever, llm_client=None)
    executor = Executor(agent_registry)
    observer = Observer(llm_client=None)
    critic = Critic(llm_client=None)
    ctx = tool_context_factory(state)

    tasks = planner.initial_plan(state)
    for t in tasks:
        state.add_task(t)
    batch = state.pop_pending_batch()

    results = await executor.execute_batch(batch, ctx, lambda *_: None)
    observer.observe_batch(results, state)
    verdict = critic.judge(state)

    assert verdict.sufficient is True
    assert len(state.tool_calls) == 1
    assert state.tool_calls[0].tool_name == "cluster_inspector"


def test_conflicting_or_missing_criteria_do_not_falsely_pass(agent_state_factory):
    state = agent_state_factory(
        goal_text="업그레이드 가능한지 분석",
        success_criteria=["설치된 컴포넌트의 목표 버전 호환성을 판정한다"],
    )
    # cluster_inspector만 성공했고 compatibility_checker는 아직 실행되지 않았다.
    state.record_tool_call(
        ToolCallRecord(id="c1", task_id="t1", tool_name="cluster_inspector", started_at=datetime.now(UTC), ok=True)
    )
    critic = Critic(llm_client=None)
    verdict = critic.judge(state)

    assert verdict.sufficient is False
