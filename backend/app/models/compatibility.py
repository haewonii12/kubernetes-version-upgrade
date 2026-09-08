from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from app.models.rag import RAGReference


class CompatibilityStatus(str, Enum):
    COMPATIBLE = "COMPATIBLE"
    INCOMPATIBLE = "INCOMPATIBLE"
    WARNING = "WARNING"
    UNKNOWN = "UNKNOWN"


class CompatibilityResult(BaseModel):
    component: str
    current_version: str | None
    target_kubernetes_version: str
    status: CompatibilityStatus
    reason: str
    recommendation: str | None = None
    sources: list[RAGReference] = Field(default_factory=list)
    # "rag" | "llm_web_search" — agi 브랜치의 Open Network 재검증/보강 결과인지 구분한다
    # (DeprecatedAPIFinding.scanned_by와 동일한 provenance 패턴). 폐쇄망 브랜치는 이
    # 필드를 채우지 않으므로 기본값 "rag"로 항상 하위 호환된다.
    verified_by: str = "rag"
