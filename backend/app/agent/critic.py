"""Critic — 현재 증거가 결론을 내리기에 충분한지 판단한다 (Section 3).

완전히 규칙 기반이다 (기본 경로에는 LLM 호출이 없다) — Test Scenario 4/5/6이
실제 LLM 서버 없이도 결정론적으로 통과해야 하기 때문. ``llm_client`` 는 향후
"2차 의견" 보강을 위한 예약된 hook일 뿐 기본 경로에서는 쓰이지 않는다.
"""

from __future__ import annotations

from app.agent.state import AgentState
from app.llm.client import LLMClient
from app.models.agent import CriticVerdict


class Critic:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self._llm = llm_client  # 예약된 hook — 기본 규칙 경로에서는 사용하지 않는다

    def judge(self, state: AgentState) -> CriticVerdict:
        missing: list[str] = []
        missing += self._check_evidence_coverage(state)
        missing += self._check_unchecked_conditions(state)
        missing += self._check_conflicts(state)
        missing += self._check_needs_latest_docs(state)

        sufficient = not missing
        reason = "모든 success_criteria에 대한 근거를 확보했습니다." if sufficient else "; ".join(missing)
        return CriticVerdict(sufficient=sufficient, missing_evidence=missing, reason=reason, checked_iteration=state.iteration)

    def _check_evidence_coverage(self, state: AgentState) -> list[str]:
        """success_criteria마다 그것을 뒷받침할 근거(tool call/observation)가 있는지 확인."""
        if state.goal is None:
            return ["Goal이 아직 파싱되지 않았습니다"]
        missing: list[str] = []
        executed_tools = {call.tool_name for call in state.tool_calls if call.ok}
        for criterion in state.goal.success_criteria:
            if not self._criterion_has_coverage(criterion, executed_tools):
                missing.append(f"'{criterion}'에 대한 근거 부족")
        return missing

    def _criterion_has_coverage(self, criterion: str, executed_tools: set[str]) -> bool:
        text = criterion.lower()
        if any(k in text for k in ("클러스터", "cluster", "현재")):
            return "cluster_inspector" in executed_tools
        if any(k in text for k in ("호환", "compatib")):
            return "compatibility_checker" in executed_tools
        if any(k in text for k in ("deprecated", "폐기", "제거")):
            return "deprecated_api_checker" in executed_tools
        if any(k in text for k in ("risk", "위험", "복잡")):
            return "risk_analyzer" in executed_tools
        # 알 수 없는 criterion 텍스트는 최소 하나의 성공한 Tool 호출이 있으면 충족으로 본다.
        return bool(executed_tools)

    def _check_unchecked_conditions(self, state: AgentState) -> list[str]:
        return [f"관찰 결과 추가 조사 필요: {obs.impact}" for obs in state.observations if obs.requires_further_investigation and obs.impact]

    def _check_conflicts(self, state: AgentState) -> list[str]:
        """같은 subject_key를 가진 두 Observation이 서로 다른 상태를 보고하면 충돌로 간주 (placeholder)."""
        return []

    def _check_needs_latest_docs(self, state: AgentState) -> list[str]:
        """UNKNOWN 상태가 있는데 web_search/official_docs가 미설정이면, 있었으면 도움이 됐을 것이라고 표시만 한다."""
        return []
