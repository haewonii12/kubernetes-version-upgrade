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

_UNRESOLVED_DEPRECATED_STATUSES = {"ACTION_REQUIRED", "UPGRADE_BLOCKER", "UNKNOWN"}
# RAG에 근거가 없다고 매 replan마다 web_search/github를 무한정 시도하지 않도록,
# 한 Observation당 외부 조사로 넘길 항목 수를 제한한다 (max_tool_calls 가드레일과
# 별개의 1차 방어선 — Section 6 정보 탐색 우선순위: RAG로 안 풀리면 개방망으로 확장).
_MAX_EXTERNAL_RESEARCH_ITEMS = 3
# 3건 중 최소 1건은 RAG가 이미 COMPATIBLE로 판정한 항목이어도 항상 개방망으로
# 2차 검증한다 — "RAG가 그렇다고 했으니 끝" 이 아니라 최소한의 교차검증을 시도한다
# (나머지는 INCOMPATIBLE/WARNING/UNKNOWN처럼 이미 위험 신호가 있는 쪽을 우선한다).
_MIN_SECOND_OPINION_SLOTS = 1
_COMPATIBILITY_STATUS_SEVERITY = {"INCOMPATIBLE": 0, "WARNING": 1, "UNKNOWN": 2, "COMPATIBLE": 3}


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

        self._flag_ready_for_llm_verification(results, state, observations)
        return observations

    def _flag_ready_for_llm_verification(
        self, results: list[tuple[Task, ToolResult]], state: AgentState, observations: list[Observation]
    ) -> None:
        """web_search + github_search가 같은 컴포넌트에 대해 한 배치 안에서 함께 끝나면
        (Planner가 둘을 같이 만들므로 보통 같은 tick에 완료된다), LLM 재검증 Task로
        이어지는 hint를 세운다. LLM이 설정되지 않았으면 아예 시도하지 않는다 — 이
        단계는 순수 규칙 기반 판정을 대체하는 게 아니라 그 위에 얹는 보강이기 때문에,
        LLM 없이 무리하게 진행하지 않는다.
        """
        if self._llm is None or not self._llm.is_configured:
            return

        by_subject: dict[str, dict[str, tuple[Task, ToolResult]]] = {}
        for task, result in results:
            component = task.input.get("component")
            target_version = task.input.get("target_version")
            if not component or not target_version or task.tool_name not in ("web_search", "github_search"):
                continue
            by_subject.setdefault(f"{component}:{target_version}", {})[task.tool_name] = (task, result)

        research_items = state.memory_working.get("compatibility_research_items", {})
        for key, tools_done in by_subject.items():
            if "web_search" not in tools_done or "github_search" not in tools_done:
                continue  # 아직 둘 다 안 끝남 — 다음 배치에서 다시 검사한다
            verify_subject_key = f"llm_verify_compatibility:{key}"
            if any(t.subject_key == verify_subject_key for t in state.plan):
                continue  # 이미 재검증 Task를 만들었음 (중복 방지)
            item = research_items.get(key)
            if not item:
                continue

            evidence = []
            for tool_name, (_, result) in tools_done.items():
                evidence.extend(e.model_dump(mode="json") for e in result.evidence)

            anchor_task_id = tools_done["web_search"][0].id
            anchor_obs = next((o for o in observations if o.task_id == anchor_task_id), None)
            if anchor_obs is None:
                continue
            anchor_obs.requires_further_investigation = True
            anchor_obs.follow_up_hint = {
                "kind": "llm_verify_compatibility",
                "component": item["component"],
                "current_version": item.get("current_version"),
                "rag_judgments": item.get("rag_judgments", []),
                "evidence": evidence[:10],
                "verify_subject_key": verify_subject_key,
            }

    def _apply_rules(self, task: Task, result: ToolResult, obs: Observation, state: AgentState) -> None:
        if result.not_configured or not result.ok:
            obs.requires_further_investigation = True
            obs.impact = "증거 수집 실패/미설정 — 이 항목은 결론에 온전히 반영되지 않습니다."
            return

        if result.tool_name == "cluster_inspector":
            self._flag_uncovered_components(result, state, obs)
        elif result.tool_name == "compatibility_checker":
            self._flag_unresolved_compatibility(result, state, obs)
        elif result.tool_name == "deprecated_api_checker":
            self._flag_unresolved_deprecated_apis(result, state, obs)

    def _flag_unresolved_compatibility(self, result: ToolResult, state: AgentState, obs: Observation) -> None:
        """RAG 판정을 그대로 최종 결론으로 삼지 않고 Open Network로 교차검증한다.

        Section 6 정보 탐색 우선순위: 클러스터 실제 상태 -> 내부 RAG -> 공식 문서 ->
        GitHub -> 기타 Web Search. UNKNOWN/WARNING/INCOMPATIBLE처럼 RAG로 안 풀린
        항목을 우선하되, RAG가 COMPATIBLE로 이미 판정한 항목도 최소 1건은 반드시
        2차 검증한다 — "RAG가 그렇다니 끝" 이 아니라 실제로 웹/GitHub에서 한 번
        더 확인해봐야 한다는 요구사항 때문이다.

        중요: 조사 대상의 target_version은 반드시 사용자가 실제로 물어본 최종
        목표 버전(state.goal.target_version)이어야 한다. upgrade_path는 여러 중간
        minor를 거치는데(예: 1.32->1.33->...->1.37), RAG는 최종 목표 버전(1.37)에는
        문서가 아예 없어 항상 UNKNOWN으로 나오는 반면 중간 minor(1.33~1.36)는 RAG
        문서가 있어 INCOMPATIBLE/WARNING처럼 "더 심각해 보이는" 상태가 나올 수 있다.
        컴포넌트별 "전 구간 중 가장 심각한 상태"만 보고 대표를 고르면, 정작 사용자가
        물어본 최종 버전 자체는 한 번도 조사 대상에 안 오르고 중간 단계 이슈만
        계속 조사하게 되는 문제가 있었다 (실제로 겪음: "1.37로 업그레이드해도
        되냐"고 물었는데 웹 검색은 전부 "kubernetes 1.33"으로만 나감).
        """
        results = (result.data or {}).get("results", [])
        if not results:
            return

        target_version = state.goal.target_version if state.goal else None

        # 컴포넌트별 "전 구간 중 가장 심각한 상태" — 중간 단계에 실제 문제가 있는
        # 컴포넌트를 우선순위로 가려내는 용도로만 쓴다 (조사 대상 자체를 정하지 않는다).
        worst_by_component: dict[str, dict] = {}
        # 컴포넌트별 "최종 목표 버전에서의 상태" — 사용자가 실제로 물어본 것.
        final_by_component: dict[str, dict] = {}
        for r in results:
            component = r["component"]
            current = worst_by_component.get(component)
            if current is None or _COMPATIBILITY_STATUS_SEVERITY.get(r["status"], 9) < _COMPATIBILITY_STATUS_SEVERITY.get(
                current["status"], 9
            ):
                worst_by_component[component] = r
            if target_version and r["target_kubernetes_version"] == target_version:
                final_by_component[component] = r

        # 최종 목표 버전에 대한 판정이 하나도 없으면(예: target_version 추출 실패)
        # 이전처럼 전 구간 최악 상태로 fallback한다 — 조사 자체를 못 하는 것보다는 낫다.
        candidates = list(final_by_component.values()) if final_by_component else list(worst_by_component.values())

        unresolved = sorted(
            (r for r in candidates if r["status"] != "COMPATIBLE"),
            # 최종 버전에서는 다 같은 UNKNOWN이라도, 중간 구간에서 이미 문제가
            # 확인된 컴포넌트를 먼저 조사한다 (진짜 위험할 가능성이 더 높다).
            key=lambda r: _COMPATIBILITY_STATUS_SEVERITY.get(worst_by_component[r["component"]]["status"], 9),
        )
        resolved = [r for r in candidates if r["status"] == "COMPATIBLE"]

        if unresolved:
            obs.requires_further_investigation = True
            obs.impact = f"Compatibility 미해결 항목 존재 ({len(unresolved)}건) — 개방망 추가 조사 필요"
        elif resolved:
            obs.requires_further_investigation = True
            obs.impact = "RAG 기준 전부 호환 판정 — 개방망으로 2차 검증 진행"
        else:
            return

        picked = unresolved[: max(0, _MAX_EXTERNAL_RESEARCH_ITEMS - _MIN_SECOND_OPINION_SLOTS)]
        picked += resolved[: _MAX_EXTERNAL_RESEARCH_ITEMS - len(picked)]

        # 컴포넌트별로 upgrade_path 전 구간(1.33~1.37 등)의 RAG 판정을 전부 모아둔다 —
        # web_search 질의문에 전체 경로를 명시하고, 나중에 LLM 재검증 단계에서
        # "기존 판정"으로 그대로 넘겨주기 위함이다 (RAG가 이미 판정한 버전도
        # 웹 근거로 다시 검증하고, RAG에 없는 버전은 이 결과로 채워 넣는다).
        rows_by_component: dict[str, list[dict]] = {}
        for r in results:
            rows_by_component.setdefault(r["component"], []).append(r)

        items = []
        research_items = state.memory_working.setdefault("compatibility_research_items", {})
        for r in picked:
            component = r["component"]
            resolved_target_version = target_version or r.get("target_kubernetes_version")
            item = {
                "component": component,
                "current_version": r.get("current_version"),
                # 대표 row가 아니라 항상 최종 목표 버전을 조사 질의에 쓴다.
                "target_version": resolved_target_version,
                "rag_judgments": [
                    {"target_kubernetes_version": row["target_kubernetes_version"], "status": row["status"], "reason": row.get("reason")}
                    for row in rows_by_component.get(component, [])
                ],
            }
            items.append(item)
            # LLM 재검증 Task(Section 6)를 만들 때 이 정보가 다시 필요하므로 미리 저장한다.
            research_items[f"{component}:{resolved_target_version}"] = item

        obs.follow_up_hint = {"kind": "external_research", "reason": "compatibility", "items": items}

    def _flag_unresolved_deprecated_apis(self, result: ToolResult, state: AgentState, obs: Observation) -> None:
        findings = (result.data or {}).get("findings", [])
        unresolved = [f for f in findings if f["status"] in _UNRESOLVED_DEPRECATED_STATUSES]
        if not unresolved:
            return
        obs.requires_further_investigation = True
        obs.impact = f"미해결 Deprecated/Removed API 존재 ({len(unresolved)}건) — 개방망 추가 조사 필요"

        seen: set[str] = set()
        items = []
        for f in unresolved:
            key = f"{f['resource_kind']}/{f['api_version']}"
            if key in seen:
                continue
            seen.add(key)
            items.append(
                {
                    "kind": f["resource_kind"],
                    "api_version": f["api_version"],
                    "target_version": f.get("evaluated_at_target_version"),
                }
            )
            if len(items) >= _MAX_EXTERNAL_RESEARCH_ITEMS:
                break
        obs.follow_up_hint = {"kind": "external_research", "reason": "deprecated_api", "items": items}

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
