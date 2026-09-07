"""Safety scaffolding (Section 8): Proposed Action -> Risk Assessment -> Human Approval -> Execution.

이번 pass는 "분석과 계획 생성까지"만 구현한다 — 즉 이 모듈의 모델들은 mutating 작업을
제안(propose)하고 기록하는 용도로만 쓰이며, 실제 실행(Execution)이나 승인 UI는
이번 범위에 포함되지 않는다. ``app.agent.executor.Executor`` 가 mutating Tool을
절대 직접 실행하지 않고 대신 ``ProposedAction`` 을 생성하는 지점에서 사용된다.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class ApprovalStatus(str, Enum):
    NOT_REQUIRED = "NOT_REQUIRED"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class RiskAssessment(BaseModel):
    severity: str  # app.models.risk.RiskSeverity 값 문자열 (순환 import 방지를 위해 직접 import 안 함)
    reason: str


class ProposedAction(BaseModel):
    """mutating 작업(delete/patch/apply/scale/rollout restart/cordon/drain/upgrade 등) 제안.

    Executor는 이 객체를 생성만 하고 절대 실행하지 않는다 (Section 8).
    """

    id: str
    description: str
    verb: str
    target: str | None = None
    command: str | None = None
    risk_assessment: RiskAssessment | None = None
    approval_status: ApprovalStatus = ApprovalStatus.PENDING
    created_at_iteration: int = 0
