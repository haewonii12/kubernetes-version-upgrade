"""자율 에이전트 실행(run) 세션 저장소 — services/session_store.py 의 새 워크플로우 버전.

기존 ``AnalysisSession``/``SessionStore`` 와 동일한 append-only 이벤트 리스트 +
0.2초 polling SSE 패턴을 그대로 따른다 — 다만 새 워크플로우 전용 ``AgentUIEvent`` 를
쌓는다는 점만 다르다. 기존 ``session_store.py`` 는 전혀 건드리지 않는다.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from app.models.agent import AgentReport, AgentUIEvent


@dataclass
class AgentRunSession:
    run_id: str
    raw_request: str
    target_version: str | None
    mock_mode: bool
    llm_endpoint: str | None = None
    llm_model: str | None = None
    status: str = "RUNNING"  # RUNNING | COMPLETED | FAILED
    events: list[AgentUIEvent] = field(default_factory=list)
    report: AgentReport | None = None
    error: str | None = None

    def emit(self, event: AgentUIEvent) -> None:
        self.events.append(event)


class AgentRunSessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, AgentRunSession] = {}

    def create(
        self,
        raw_request: str,
        target_version: str | None,
        mock_mode: bool,
        llm_endpoint: str | None = None,
        llm_model: str | None = None,
    ) -> AgentRunSession:
        session = AgentRunSession(
            run_id=str(uuid.uuid4()),
            raw_request=raw_request,
            target_version=target_version,
            mock_mode=mock_mode,
            llm_endpoint=llm_endpoint,
            llm_model=llm_model,
        )
        self._sessions[session.run_id] = session
        return session

    def get(self, run_id: str) -> AgentRunSession | None:
        return self._sessions.get(run_id)


agent_session_store = AgentRunSessionStore()
