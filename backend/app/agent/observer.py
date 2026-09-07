"""Observer — Tool 결과를 의미 있는 Observation으로 변환한다 (Section 3).

기본 경로는 완전히 규칙 기반/결정론적이다 (Test Scenario 3/4/5/6이 LLM 없이도
안정적으로 동작해야 하기 때문). ``llm_client`` 는 향후 자유 텍스트(web search 등)
해석을 보강하기 위한 hook으로만 남겨둔다.
"""

from __future__ import annotations

import uuid

from app.agent.state import AgentState
from app.llm.client import LLMClient
from app.models.agent import Observation, Task, ToolResult

_UNRESOLVED_COMPATIBILITY_STATUSES = {"WARNING", "INCOMPATIBLE", "UNKNOWN"}
_UNRESOLVED_DEPRECATED_STATUSES = {"ACTION_REQUIRED", "UPGRADE_BLOCKER", "UNKNOWN"}


class Observer:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self._llm = llm_client  # 예약된 hook — 기본 규칙 경로에서는 사용하지 않는다

    def observe_batch(self, results: list[tuple[Task, ToolResult]], state: AgentState) -> list[Observation]:
        observations: list[Observation] = []
        for task, result in results:
            obs = Observation(
                id=uuid.uuid4().hex[:12],
                task_id=task.id,
                tool_name=result.tool_name,
                observation=result.summary,
                expected=task.expected_outcome,
                actual=result.summary,
                evidence=result.evidence,
                created_at_iteration=state.iteration,
            )
            self._apply_rules(task, result, obs, state)
            state.add_observation(obs)
            state.add_evidence(result.evidence)
            observations.append(obs)
        return observations

    def _apply_rules(self, task: Task, result: ToolResult, obs: Observation, state: AgentState) -> None:
        if result.not_configured or not result.ok:
            obs.requires_further_investigation = True
            obs.impact = "증거 수집 실패/미설정 — 이 항목은 결론에 온전히 반영되지 않습니다."
            return

        if result.tool_name == "cluster_inspector":
            self._flag_uncovered_components(result, state, obs)
        elif result.tool_name == "compatibility_checker":
            statuses = {r["status"] for r in (result.data or {}).get("results", [])}
            if statuses & _UNRESOLVED_COMPATIBILITY_STATUSES:
                obs.requires_further_investigation = True
                obs.impact = "Compatibility 미해결 항목 존재"
        elif result.tool_name == "deprecated_api_checker":
            findings = (result.data or {}).get("findings", [])
            if any(f["status"] in _UNRESOLVED_DEPRECATED_STATUSES for f in findings):
                obs.requires_further_investigation = True
                obs.impact = "미해결 Deprecated/Removed API 존재"

    def _flag_uncovered_components(self, result: ToolResult, state: AgentState, obs: Observation) -> None:
        """새로 발견된(아직 Compatibility 확인 Task가 없는) 컴포넌트가 있으면 follow_up_hint를 세운다.

        한 Observation당 hint 하나만 세운다 — Planner.replan()이 매 iteration마다
        호출되므로, 나머지 미확인 컴포넌트는 다음 cycle에 순차적으로 잡힌다
        (max_iterations 가드레일로 상한이 걸린다).

        이미 넓은 범위(subject_key=="compatibility")의 compatibility_checker Task가
        계획에 있으면 그 Task가 모든 컴포넌트를 이미 커버하므로 아무것도 플래그하지
        않는다 — 그렇지 않으면(Scenario 1처럼 compatibility가 애초에 계획에 없던
        좁은 목표) 새로 발견된 컴포넌트 하나를 골라 후속 확인을 요청한다
        (Scenario 3).

        Goal에 target_version이 아예 없으면(순수 현황 파악 목표) compatibility 자체가
        의미가 없으므로 절대 플래그하지 않는다 — Scenario 1("필요 이상으로 upgrade
        workflow를 수행하면 안 된다")과 Scenario 3("업그레이드 관련 목표에서는 새
        컴포넌트 발견 시 동적으로 확인한다")을 동시에 만족시키는 지점이다.
        """
        if state.goal is None or state.goal.target_version is None:
            return
        has_broad_compatibility_task = any(t.subject_key == "compatibility" for t in state.plan)
        if has_broad_compatibility_task:
            return
        checked = {t.subject_key for t in state.plan if t.subject_key and t.subject_key.startswith("compatibility:")}
        cluster = (result.data or {}).get("cluster", {})
        for sw in cluster.get("software_inventory", []):
            key = f"compatibility:{sw['name'].lower()}:{sw.get('version')}"
            if key in checked:
                continue
            obs.requires_further_investigation = True
            obs.follow_up_hint = {"kind": "compatibility", "component": sw["name"].lower(), "version": sw.get("version")}
            obs.impact = f"신규 컴포넌트 {sw['name']} {sw.get('version')} — Compatibility 미확인"
            return
