"""내부 AgentEventType -> UI AgentUIEvent 매핑 (Section 12).

``analysis_service.py`` 의 ``_NODE_STAGE_MAP`` (LangGraph 노드 이름 -> AnalysisStage)과
동일한 역할을 한다 — 내부 이벤트 구조가 바뀌어도 이 함수 하나만 고치면 되고,
프론트엔드 계약(AgentUIEvent)은 그대로 유지된다.
"""

from __future__ import annotations

from app.agent.state import AgentState
from app.models.agent import AgentEvent, AgentEventType, AgentUIEvent

_STAGE_BY_TYPE: dict[AgentEventType, str] = {
    AgentEventType.GOAL_CREATED: "GOAL",
    AgentEventType.PLANNING: "PLANNING",
    AgentEventType.TASK_CREATED: "PLANNING",
    AgentEventType.TOOL_SELECTED: "EXECUTING",
    AgentEventType.TOOL_STARTED: "EXECUTING",
    AgentEventType.TOOL_COMPLETED: "EXECUTING",
    AgentEventType.OBSERVATION_CREATED: "OBSERVING",
    AgentEventType.CRITIC_STARTED: "EVALUATING",
    AgentEventType.REPLANNING: "PLANNING",
    AgentEventType.TASK_COMPLETED: "EXECUTING",
    AgentEventType.GOAL_COMPLETED: "COMPLETED",
    AgentEventType.ERROR: "FAILED",
}


def map_internal_event_to_ui(event: AgentEvent, state: AgentState) -> AgentUIEvent:
    stage = _STAGE_BY_TYPE.get(event.type, "EXECUTING")
    if stage == "COMPLETED":
        progress = 100
    else:
        progress = min(95, int(5 + (state.iteration / max(state.max_iterations, 1)) * 90))
    return AgentUIEvent(
        stage=stage,
        event_type=event.type.value,
        message=event.message,
        timestamp=event.timestamp,
        progress=progress,
        iteration=state.iteration,
        detail=event.payload,
    )
