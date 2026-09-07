"""Test Scenario 1/2: Planner는 Goal에 필요한 Task만 생성해야 한다."""

from __future__ import annotations

from app.agent.goal_manager import GoalManager
from app.agent.planner import Planner


def test_narrow_goal_produces_only_inspection_task(tool_retriever, agent_state_factory):
    goal_manager = GoalManager(llm_client=None)
    goal = goal_manager.parse_goal("현재 클러스터 상태만 분석해줘", None)

    state = agent_state_factory(goal_text=goal.goal, target_version=goal.target_version, success_criteria=goal.success_criteria)
    state.set_goal(goal)

    planner = Planner(tool_retriever, llm_client=None)
    tasks = planner.initial_plan(state)

    assert [t.tool_name for t in tasks] == ["cluster_inspector"]


def test_upgrade_feasibility_goal_produces_full_task_set(tool_retriever, agent_state_factory):
    goal_manager = GoalManager(llm_client=None)
    goal = goal_manager.parse_goal("현재 Kubernetes 1.32 클러스터를 1.37로 업그레이드해도 되는지 분석해줘", "1.37")

    state = agent_state_factory(goal_text=goal.goal, target_version=goal.target_version, success_criteria=goal.success_criteria)
    state.set_goal(goal)

    planner = Planner(tool_retriever, llm_client=None)
    tasks = planner.initial_plan(state)
    tool_names = {t.tool_name for t in tasks}

    assert {"cluster_inspector", "compatibility_checker", "deprecated_api_checker"} <= tool_names
