"""Goal-driven Autonomous Agent 서브시스템의 Pydantic 스키마 (agi 브랜치).

기존 폐쇄망 워크플로우(``app.models.report`` / ``app.models.upgrade``)와는 별도의 모델
집합이다 — 고정 워크플로우의 ``AnalysisStage``/``UpgradeReport`` 를 재사용하지 않고,
Goal/Task/Observation 기반의 자율 루프 전용 스키마를 정의한다 (Section 10, 11 참고).

용어 주의: 이 모듈이 구현하는 것은 실제 AGI가 아니라 "Autonomous/Cognitive/Goal-driven
Agent" 다. 코드/문서 어디에도 "AGI를 구현했다"는 표현을 쓰지 않는다.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.models.agent_safety import ProposedAction
from app.models.risk import ReadinessScore, RiskFinding


class ToolCapability(str, Enum):
    """AgentTool이 선언하는 역량 태그. Planner/ToolRetriever가 Task -> Tool 매핑에 사용."""

    CLUSTER_READ = "cluster_read"
    COMPATIBILITY = "compatibility"
    DEPRECATED_API = "deprecated_api"
    RISK = "risk"
    KNOWLEDGE_SEARCH = "knowledge_search"
    WEB_SEARCH = "web_search"
    OFFICIAL_DOCS = "official_docs"
    SOURCE_CODE = "source_code"
    OBSERVABILITY = "observability"
    GITOPS = "gitops"


class Goal(BaseModel):
    """자연어 요청을 GoalManager가 구조화한 결과. success_criteria가 goal 완료 판정 기준이 된다."""

    goal: str
    target_version: str | None = None
    success_criteria: list[str] = Field(default_factory=list)
    created_at: datetime


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class Task(BaseModel):
    """Planner가 생성하는 실행 단위. tool_name은 Planner가 미리 확정한다 — Executor는 조회만 한다."""

    id: str
    description: str
    capability_hint: ToolCapability | None = None
    tool_name: str | None = None
    input: dict[str, Any] = Field(default_factory=dict)
    expected_outcome: str | None = None
    status: TaskStatus = TaskStatus.PENDING
    origin: str = "initial"  # "initial" | "replan"
    subject_key: str | None = None  # replan 중복 방지용 dedup key (예: "compatibility:calico:3.30.7")
    created_at_iteration: int = 0


class Evidence(BaseModel):
    """모든 판단/결론에 첨부되는 근거 (Section 6 provenance 요구사항)."""

    source_type: str  # "rag" | "cluster" | "web_search" | "official_docs" | "github" | "internal"
    title: str
    url: str | None = None
    doc_id: str | None = None
    excerpt: str | None = None
    retrieved_at: datetime | None = None

    @classmethod
    def from_rag_reference(cls, ref: Any) -> "Evidence":
        """``app.models.rag.RAGReference`` 를 새 Evidence 모델로 변환 (폐쇄망 브랜치 근거와의 다리)."""
        return cls(
            source_type="rag",
            title=ref.document,
            doc_id=ref.doc_id,
            excerpt=ref.excerpt,
        )


class ToolResult(BaseModel):
    """AgentTool.execute()의 반환값. not_configured=True면 실패가 아니라 '설정 안 됨' (LLMClient와 동일 철학)."""

    tool_name: str
    ok: bool
    data: dict[str, Any] | None = None
    summary: str
    evidence: list[Evidence] = Field(default_factory=list)
    error: str | None = None
    not_configured: bool = False


class ToolCallRecord(BaseModel):
    id: str
    task_id: str
    tool_name: str
    started_at: datetime
    finished_at: datetime | None = None
    ok: bool | None = None
    not_configured: bool = False
    error: str | None = None


class Observation(BaseModel):
    """Observer가 ToolResult를 의미있는 상태로 변환한 결과 (Section 3 Observer 요구사항)."""

    id: str
    task_id: str
    tool_name: str
    observation: str
    expected: str | None = None
    actual: str | None = None
    impact: str | None = None
    requires_further_investigation: bool = False
    follow_up_hint: dict[str, Any] | None = None
    evidence: list[Evidence] = Field(default_factory=list)
    created_at_iteration: int = 0


class CriticVerdict(BaseModel):
    sufficient: bool
    missing_evidence: list[str] = Field(default_factory=list)
    reason: str
    checked_iteration: int


class AgentEventType(str, Enum):
    """내부 전용 이벤트 타입 — 프론트로 직접 전달되지 않는다 (agent/events.py가 UI 이벤트로 매핑)."""

    GOAL_CREATED = "goal_created"
    PLANNING = "planning"
    TASK_CREATED = "task_created"
    TOOL_SELECTED = "tool_selected"
    TOOL_STARTED = "tool_started"
    TOOL_COMPLETED = "tool_completed"
    OBSERVATION_CREATED = "observation_created"
    CRITIC_STARTED = "critic_started"
    REPLANNING = "replanning"
    TASK_COMPLETED = "task_completed"
    GOAL_COMPLETED = "goal_completed"
    ERROR = "error"


class AgentEvent(BaseModel):
    """내부 이벤트. app.agent.events.map_internal_event_to_ui()로만 UI에 노출된다."""

    type: AgentEventType
    message: str
    timestamp: datetime
    iteration: int
    payload: dict[str, Any] = Field(default_factory=dict)


class AgentUIEvent(BaseModel):
    """SSE로 프론트에 실제 전송되는 페이로드. AnalysisEvent(report.py)의 새 워크플로우 버전."""

    stage: str  # GOAL | PLANNING | EXECUTING | OBSERVING | EVALUATING | REPLANNING | COMPLETED | FAILED
    event_type: str
    message: str
    timestamp: datetime
    progress: int
    iteration: int
    detail: dict[str, Any] = Field(default_factory=dict)


class FinalConclusion(BaseModel):
    summary: str
    goal_met: bool
    missing_evidence: list[str] = Field(default_factory=list)
    citations: list[Evidence] = Field(default_factory=list)
    stopped_reason: str  # "critic_sufficient" | "max_iterations" | "max_tool_calls" | "planner_exhausted" | "error"
    # 프론트가 summary 문자열을 파싱하지 않고 바로 카드/뱃지로 렌더링할 수 있도록,
    # risk_analyzer/compatibility_checker/deprecated_api_checker가 이미 계산해 둔
    # 구조화된 결과를 그대로 노출한다 (app.models.risk 재사용, 재구현 아님).
    readiness: ReadinessScore | None = None
    risks: list[RiskFinding] = Field(default_factory=list)  # 심각도순 전체 목록 (dedup만 적용, 개수 제한 없음)
    unresolved_components: list[str] = Field(default_factory=list)
    deprecated_action_required_count: int = 0


class AgentReport(BaseModel):
    run_id: str
    created_at: datetime
    goal: Goal
    plan_history: list[Task] = Field(default_factory=list)
    observations: list[Observation] = Field(default_factory=list)
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    final_conclusion: FinalConclusion
    proposed_actions: list[ProposedAction] = Field(default_factory=list)
