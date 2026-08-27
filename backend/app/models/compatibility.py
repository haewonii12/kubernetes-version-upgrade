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
