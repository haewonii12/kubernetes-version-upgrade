"""Test Scenario 3: 실행 중 새 컴포넌트(Calico 3.30.7)를 발견하면 최초 Plan에 없던
compatibility 확인 Task가 동적으로 추가되어야 한다.

Observer의 규칙(``_flag_uncovered_components``)과 Planner의 재계획
(``replan``/``_task_from_observation``)을 직접 단위 테스트한다 — 실제 클러스터/LLM
없이 완전히 결정론적이다.
"""

from __future__ import annotations

from app.agent.observer import Observer
from app.agent.planner import Planner
from app.models.agent import Task, TaskStatus, ToolResult


def _cluster_inspector_result_with_calico() -> ToolResult:
    return ToolResult(
        tool_name="cluster_inspector",
        ok=True,
        data={
            "cluster": {
                "software_inventory": [
                    {"name": "Calico", "version": "3.30.7", "namespace": "kube-system"},
                ]
            },
            "node_warnings": [],
        },
        summary="Kubernetes 1.32.13, CNI=Calico 확인",
    )


def test_calico_discovery_flags_follow_up_investigation(agent_state_factory):
    # target_version이 있는 목표지만, 초기 계획에는 compatibility 카테고리가 없다
    # (Scenario 1처럼 좁게 시작했다가, 실행 중 발견으로 넓어지는 경우를 재현).
    state = agent_state_factory(goal_text="클러스터 노드 목록만 보여줘", target_version="1.37", success_criteria=["노드 목록을 보여준다"])
    inspect_task = Task(id="t1", description="클러스터 현재 상태 수집", tool_name="cluster_inspector", subject_key="inspect_cluster")
    state.add_task(inspect_task)
    inspect_task.status = TaskStatus.DONE

    observer = Observer(llm_client=None)
    observations = observer.observe_batch([(inspect_task, _cluster_inspector_result_with_calico())], state)

    assert len(observations) == 1
    obs = observations[0]
    assert obs.requires_further_investigation is True
    assert obs.follow_up_hint == {"kind": "compatibility", "component": "calico", "version": "3.30.7"}


def test_planner_replan_adds_new_task_not_in_initial_plan(tool_retriever, agent_state_factory):
    state = agent_state_factory(goal_text="클러스터 노드 목록만 보여줘", target_version="1.37", success_criteria=["노드 목록을 보여준다"])
    inspect_task = Task(id="t1", description="클러스터 현재 상태 수집", tool_name="cluster_inspector", subject_key="inspect_cluster")
    state.add_task(inspect_task)
    inspect_task.status = TaskStatus.DONE

    observer = Observer(llm_client=None)
    observer.observe_batch([(inspect_task, _cluster_inspector_result_with_calico())], state)

    initial_task_count = len(state.plan)
    planner = Planner(tool_retriever, llm_client=None)
    new_tasks = planner.replan(state)
    added = [t for t in new_tasks if state.add_task(t)]

    assert len(added) == 1
    new_task = added[0]
    assert new_task.tool_name == "compatibility_checker"
    assert new_task.subject_key == "compatibility:calico:3.30.7"
    assert new_task.origin == "replan"
    assert len(state.plan) == initial_task_count + 1

    # idempotent: 같은 관찰을 다시 replan해도 중복 추가되지 않는다.
    more_tasks = planner.replan(state)
    added_again = [t for t in more_tasks if state.add_task(t)]
    assert added_again == []


def _compatibility_result_with_unresolved_items() -> ToolResult:
    return ToolResult(
        tool_name="compatibility_checker",
        ok=True,
        data={
            "results": [
                {"component": "kube-proxy", "current_version": "1.32.13", "target_kubernetes_version": "1.36", "status": "UNKNOWN"},
                {"component": "rhel", "current_version": "8.10", "target_kubernetes_version": "1.36", "status": "WARNING"},
            ]
        },
        summary="Compatibility 2건 판정 완료 (주의 필요 2건)",
    )


def test_unresolved_compatibility_escalates_to_web_and_github_search(agent_state_factory, tool_retriever):
    """RAG로 못 푼 Compatibility 항목은 web_search/github_search Task로 이어져야 한다
    (RAG 근거가 없다고 그냥 UNKNOWN으로 끝내면 안 된다 — Section 6 정보 탐색 우선순위)."""
    state = agent_state_factory(goal_text="1.32에서 1.36으로 업그레이드 가능한지 분석", target_version="1.36")
    compat_task = Task(id="t1", description="compat", tool_name="compatibility_checker", subject_key="compatibility")
    state.add_task(compat_task)

    observer = Observer(llm_client=None)
    observations = observer.observe_batch([(compat_task, _compatibility_result_with_unresolved_items())], state)

    obs = observations[0]
    assert obs.requires_further_investigation is True
    assert obs.follow_up_hint["kind"] == "external_research"
    assert obs.follow_up_hint["reason"] == "compatibility"
    assert {item["component"] for item in obs.follow_up_hint["items"]} == {"kube-proxy", "rhel"}

    planner = Planner(tool_retriever, llm_client=None)
    new_tasks = planner.replan(state)
    added = [t for t in new_tasks if state.add_task(t)]

    tool_names = sorted(t.tool_name for t in added)
    assert tool_names == ["github_search", "github_search", "web_search", "web_search"]
    assert all(t.origin == "replan" for t in added)
    assert all("kubernetes 1.36 compatibility" in t.input["query"] for t in added)


def _compatibility_result_all_compatible() -> ToolResult:
    return ToolResult(
        tool_name="compatibility_checker",
        ok=True,
        data={
            "results": [
                {"component": "calico", "current_version": "3.30.7", "target_kubernetes_version": "1.36", "status": "COMPATIBLE"},
                {"component": "containerd", "current_version": "1.7.20", "target_kubernetes_version": "1.36", "status": "COMPATIBLE"},
            ]
        },
        summary="Compatibility 2건 판정 완료 (주의 필요 0건)",
    )


def test_fully_compatible_result_still_gets_second_opinion(agent_state_factory):
    """RAG가 전부 COMPATIBLE로 판정해도 '그걸로 끝'이 아니라 최소 1건은 개방망으로
    2차 검증해야 한다 — RAG 판정만 믿고 결론 내리지 않는다."""
    state = agent_state_factory(goal_text="1.32에서 1.36으로 업그레이드 가능한지 분석", target_version="1.36")
    compat_task = Task(id="t1", description="compat", tool_name="compatibility_checker", subject_key="compatibility")
    state.add_task(compat_task)

    observer = Observer(llm_client=None)
    observations = observer.observe_batch([(compat_task, _compatibility_result_all_compatible())], state)

    obs = observations[0]
    assert obs.requires_further_investigation is True
    assert obs.follow_up_hint["kind"] == "external_research"
    assert len(obs.follow_up_hint["items"]) >= 1
