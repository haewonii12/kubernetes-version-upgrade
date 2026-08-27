from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from app.models.rag import RAGReference


class RiskSeverity(str, Enum):
    BLOCKER = "BLOCKER"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


_SEVERITY_WEIGHT: dict[RiskSeverity, int] = {
    RiskSeverity.BLOCKER: 20,
    RiskSeverity.HIGH: 8,
    RiskSeverity.MEDIUM: 3,
    RiskSeverity.LOW: 1,
    RiskSeverity.INFO: 0,
}


class RiskFinding(BaseModel):
    finding: str
    severity: RiskSeverity
    category: str
    reason: str
    recommendation: str
    sources: list[RAGReference] = Field(default_factory=list)
    related_upgrade_step: str | None = None


class ReadinessScore(BaseModel):
    score: int
    blocker_count: int
    high_count: int
    medium_count: int
    low_count: int
    info_count: int

    @classmethod
    def from_findings(cls, findings: list[RiskFinding]) -> "ReadinessScore":
        counts = {s: 0 for s in RiskSeverity}
        for f in findings:
            counts[f.severity] += 1
        deduction = sum(_SEVERITY_WEIGHT[s] * n for s, n in counts.items())
        score = max(0, 100 - deduction)
        return cls(
            score=score,
            blocker_count=counts[RiskSeverity.BLOCKER],
            high_count=counts[RiskSeverity.HIGH],
            medium_count=counts[RiskSeverity.MEDIUM],
            low_count=counts[RiskSeverity.LOW],
            info_count=counts[RiskSeverity.INFO],
        )
