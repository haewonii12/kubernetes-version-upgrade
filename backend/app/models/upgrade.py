from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from app.models.compatibility import CompatibilityResult
from app.models.rag import RAGReference
from app.models.risk import RiskFinding


class DeprecatedAPIStatus(str, Enum):
    OK = "OK"
    ACTION_REQUIRED = "ACTION_REQUIRED"
    UPGRADE_BLOCKER = "UPGRADE_BLOCKER"
    UNKNOWN = "UNKNOWN"


class DeprecatedAPIFinding(BaseModel):
    resource_kind: str
    api_version: str
    resource_name: str | None = None
    namespace: str | None = None
    deprecated_in_version: str | None = None
    removed_in_version: str | None = None
    replacement_api_version: str | None = None
    status: DeprecatedAPIStatus
    evaluated_at_target_version: str | None = None
    sources: list[RAGReference] = Field(default_factory=list)


class UpgradeCommand(BaseModel):
    description: str
    command: str
    target: str | None = None


class PreCheckStatus(str, Enum):
    PENDING = "PENDING"
    PASS_ = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"


class CheckItem(BaseModel):
    """Pre/Post Check 항목. PoC(Read-Only)에서는 command 실행 없이 제안만 한다."""

    description: str
    command: str | None = None
    status: PreCheckStatus = PreCheckStatus.PENDING


class NodeUpgradeStep(BaseModel):
    node: str
    order: int
    commands: list[UpgradeCommand] = Field(default_factory=list)
    verification: list[str] = Field(default_factory=list)


class VersionUpgradePhase(BaseModel):
    phase_number: int
    from_version: str
    to_version: str
    release_note_summary: str | None = None
    # "llm" = LLM이 RAG 근거를 바탕으로 생성한 요약, "excerpt" = 검색된 문서 원문 발췌.
    # 프론트에서 생성된 텍스트임을 숨기지 않고 배지로 구분 표시하기 위한 필드 (Section 24).
    release_note_summary_source: str | None = None
    deprecated_apis: list[DeprecatedAPIFinding] = Field(default_factory=list)
    compatibility_results: list[CompatibilityResult] = Field(default_factory=list)
    pre_checks: list[CheckItem] = Field(default_factory=list)
    control_plane_steps: list[NodeUpgradeStep] = Field(default_factory=list)
    worker_steps: list[NodeUpgradeStep] = Field(default_factory=list)
    post_checks: list[CheckItem] = Field(default_factory=list)
    risks: list[RiskFinding] = Field(default_factory=list)
    sources: list[RAGReference] = Field(default_factory=list)


class UpgradePlan(BaseModel):
    current_version: str
    target_version: str
    upgrade_path: list[str] = Field(default_factory=list)
    phases: list[VersionUpgradePhase] = Field(default_factory=list)
