"""Planner — 고정 workflow 없이 AgentState/Goal로부터 동적으로 Task를 생성한다 (Section 3).

두 가지 진입점만 있다:
  - ``initial_plan``: 최초 계획. Goal의 텍스트를 규칙 기반으로 분류해 필요한 Task
    카테고리만 고른다 (좁은 목표 -> 좁은 계획, Test Scenario 1/2).
  - ``replan``: 이후 매 iteration마다 호출된다. ``state.observations`` 중
    ``requires_further_investigation`` 이 세워진 것을 읽어 새 Task를 만든다.
    ``AgentState.add_task`` 가 ``subject_key`` 로 중복을 걸러주므로 매 cycle 호출해도
    안전하다 (idempotent).

Task.tool_name은 Planner가 ToolRetriever로 미리 확정한다 — Executor는 조회만 한다.
"""

from __future__ import annotations

import uuid

from app.agent.state import AgentState
from app.agent.tools import ToolRetriever
from app.llm.client import LLMClient
from app.models.agent import Goal, Observation, Task, ToolCapability

# 카테고리 순서가 실행 순서다 — risk는 compatibility/deprecated_api 결과를 필요로 하므로
# 항상 마지막에 온다 (Executor.execute_batch는 배치를 리스트 순서대로 실행한다).
_CATEGORY_ORDER = ["inspect_cluster", "compatibility", "deprecated_api", "risk"]

_CATEGORY_SPEC: dict[str, tuple[ToolCapability, str, str]] = {
    "inspect_cluster": (ToolCapability.CLUSTER_READ, "cluster_inspector", "클러스터 현재 상태 수집"),
    "compatibility": (ToolCapability.COMPATIBILITY, "compatibility_checker", "설치된 컴포넌트 Compatibility 판정"),
    "deprecated_api": (ToolCapability.DEPRECATED_API, "deprecated_api_checker", "Deprecated/Removed API 검사"),
    "risk": (ToolCapability.RISK, "risk_analyzer", "종합 Risk 및 준비 복잡도 산정"),
}


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


class Planner:
    def __init__(self, tool_retriever: ToolRetriever, llm_client: LLMClient | None = None) -> None:
        self._tool_retriever = tool_retriever
        self._llm = llm_client  # 향후 LLM 보강용 hook — 기본 경로는 규칙 기반

    def initial_plan(self, state: AgentState) -> list[Task]:
        assert state.goal is not None
        categories = self._infer_task_categories(state.goal)
        tasks: list[Task] = []
        for category in categories:
            task = self._tasks_for_category(category, state)
            if task is not None:
                tasks.append(task)
        return tasks

    def replan(self, state: AgentState) -> list[Task]:
        new_tasks: list[Task] = []
        for obs in state.observations:
            if not obs.requires_further_investigation:
                continue
            new_tasks.extend(self._tasks_from_observation(obs, state))
        return new_tasks

    def _infer_task_categories(self, goal: Goal) -> list[str]:
        """규칙 기반 분류 — 좁은 목표에는 좁은 Task만, 넓은(업그레이드) 목표에는 필요한 만큼만."""
        text = (goal.goal + " " + " ".join(goal.success_criteria)).lower()
        categories: list[str] = ["inspect_cluster"]  # 클러스터를 안 보고 시작할 수는 없다

        if any(k in text for k in ("호환", "compatib")):
            categories.append("compatibility")
        if any(k in text for k in ("deprecated", "폐기", "제거된 api", "removed api")):
            categories.append("deprecated_api")
        if any(k in text for k in ("risk", "위험", "복잡")):
            categories.append("risk")

        is_upgrade_feasibility = goal.target_version is not None and any(
            k in text for k in ("업그레이드", "upgrade", "feasib", "가능", "이관")
        )
        if is_upgrade_feasibility:
            categories += ["compatibility", "deprecated_api", "risk"]

        seen: set[str] = set()
        ordered = [c for c in _CATEGORY_ORDER if c in categories and not (c in seen or seen.add(c))]
        return ordered

    def _tasks_for_category(self, category: str, state: AgentState) -> Task | None:
        capability, preferred_tool, description = _CATEGORY_SPEC[category]
        candidates = self._tool_retriever.retrieve(description, top_k=1, required_capabilities=[capability])
        tool_name = candidates[0].name if candidates else preferred_tool

        task_input: dict = {}
        if category in ("compatibility", "deprecated_api") and state.goal and state.goal.target_version:
            task_input["target_version"] = state.goal.target_version

        return Task(
            id=_new_id(),
            description=description,
            capability_hint=capability,
            tool_name=tool_name,
            input=task_input,
            origin="initial",
            subject_key=category,
            created_at_iteration=state.iteration,
        )

    def _tasks_from_observation(self, obs: Observation, state: AgentState) -> list[Task]:
        hint = obs.follow_up_hint
        if not hint:
            return []

        kind = hint.get("kind")
        if kind == "compatibility":
            return self._tasks_for_new_component(hint, state)
        if kind == "external_research":
            return self._tasks_for_external_research(hint, state)
        return []

    def _tasks_for_new_component(self, hint: dict, state: AgentState) -> list[Task]:
        component = hint["component"]
        version = hint.get("version")
        key = f"compatibility:{component}:{version}"
        if any(t.subject_key == key for t in state.plan):
            return []
        task_input: dict = {"component": component, "component_version": version}
        if state.goal and state.goal.target_version:
            task_input["target_version"] = state.goal.target_version
        return [
            Task(
                id=_new_id(),
                description=f"{component} {version or ''} 목표 버전 호환성 재확인".strip(),
                capability_hint=ToolCapability.COMPATIBILITY,
                tool_name="compatibility_checker",
                input=task_input,
                origin="replan",
                subject_key=key,
                created_at_iteration=state.iteration,
            )
        ]

    def _tasks_for_external_research(self, hint: dict, state: AgentState) -> list[Task]:
        """RAG(내부 지식)로 못 푼 항목을 Web Search/GitHub로 넘긴다 (Section 6).

        Observer가 이미 항목 수를 제한해서 넘기므로(``_MAX_EXTERNAL_RESEARCH_ITEMS``)
        여기서는 항목마다 web_search + github_search Task 두 개를 만들기만 한다 —
        각 Tool은 API 키/설정이 없으면 스스로 not_configured로 안전하게 끝난다.
        """
        reason = hint.get("reason")
        tasks: list[Task] = []
        for item in hint.get("items", []):
            if reason == "compatibility":
                subject = f"{item['component']}:{item.get('target_version')}"
                query = (
                    f"{item['component']} {item.get('current_version') or ''} kubernetes "
                    f"{item.get('target_version')} compatibility".strip()
                )
                description = f"{item['component']} Kubernetes {item.get('target_version')} 호환성 웹 조사"
            elif reason == "deprecated_api":
                subject = f"{item['kind']}/{item['api_version']}:{item.get('target_version')}"
                query = f"{item['kind']} {item['api_version']} kubernetes {item.get('target_version')} deprecated removed"
                description = f"{item['kind']}/{item['api_version']} deprecation 관련 웹 조사"
            else:
                continue

            for tool_name in ("web_search", "github_search"):
                key = f"external_research:{tool_name}:{subject}"
                if any(t.subject_key == key for t in state.plan):
                    continue
                tasks.append(
                    Task(
                        id=_new_id(),
                        description=description,
                        capability_hint=(
                            ToolCapability.WEB_SEARCH if tool_name == "web_search" else ToolCapability.SOURCE_CODE
                        ),
                        tool_name=tool_name,
                        input={"query": query},
                        origin="replan",
                        subject_key=key,
                        created_at_iteration=state.iteration,
                    )
                )
        return tasks
