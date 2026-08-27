"""분석 세션(진행 상태/SSE 이벤트/결과)을 메모리에 보관한다.

PoC 범위이므로 프로세스 재시작 시 세션은 사라진다. 완료된 결과는
Section 32 Cluster Snapshot으로 디스크에도 별도 저장되어 재조회가 가능하다.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.models.report import AnalysisEvent, AnalysisStage, UpgradeReport


@dataclass
class AnalysisSession:
    analysis_id: str
    target_version: str
    mock_mode: bool
    llm_endpoint: str | None = None
    llm_model: str | None = None
    status: str = "RUNNING"  # RUNNING | COMPLETED | FAILED
    events: list[AnalysisEvent] = field(default_factory=list)
    report: UpgradeReport | None = None
    error: str | None = None

    def emit(self, stage: AnalysisStage, message: str, progress: int) -> None:
        # SSE 구독자는 events 리스트를 인덱스 기반으로 폴링한다 (services/analysis_service.py
        # 참고) — 재연결 시에도 처음부터 재생 가능하도록 Queue 대신 append-only 리스트를 쓴다.
        self.events.append(AnalysisEvent(stage=stage, message=message, timestamp=datetime.now(UTC), progress=progress))


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, AnalysisSession] = {}

    def create(
        self,
        target_version: str,
        mock_mode: bool,
        llm_endpoint: str | None = None,
        llm_model: str | None = None,
    ) -> AnalysisSession:
        session = AnalysisSession(
            analysis_id=str(uuid.uuid4()),
            target_version=target_version,
            mock_mode=mock_mode,
            llm_endpoint=llm_endpoint,
            llm_model=llm_model,
        )
        self._sessions[session.analysis_id] = session
        return session

    def get(self, analysis_id: str) -> AnalysisSession | None:
        return self._sessions.get(analysis_id)


session_store = SessionStore()
