from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, model_validator

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


class ComplexityFactor(BaseModel):
    """준비 복잡도(%)에 각 심각도가 얼마나 기여했는지 — UI 툴팁 근거용."""

    severity: RiskSeverity
    count: int
    weight: int  # 심각도 1건당 가중치
    points: int  # count * weight


class ReadinessScore(BaseModel):
    # score: 높을수록 준비됨 (100 - 감점). 하위 호환을 위해 유지 (snapshot 목록/LLM 요약이 사용).
    score: int
    # complexity: 낮을수록 준비 작업이 단순, 높을수록 복잡/많음 (0~100%). 대시보드 헤드라인 지표.
    complexity: int = -1
    blocker_count: int
    high_count: int
    medium_count: int
    low_count: int
    info_count: int
    complexity_factors: list[ComplexityFactor] = Field(default_factory=list)

    @model_validator(mode="after")
    def _backfill_complexity(self) -> "ReadinessScore":
        # complexity 필드가 없던 시절의 snapshot을 로드할 때 score로부터 역산한다.
        if self.complexity < 0:
            self.complexity = min(100, max(0, 100 - self.score))
        return self

    @classmethod
    def from_findings(cls, findings: list[RiskFinding]) -> "ReadinessScore":
        counts = {s: 0 for s in RiskSeverity}
        for f in findings:
            counts[f.severity] += 1
        factors = [
            ComplexityFactor(
                severity=s,
                count=counts[s],
                weight=_SEVERITY_WEIGHT[s],
                points=_SEVERITY_WEIGHT[s] * counts[s],
            )
            for s in RiskSeverity
            if counts[s] > 0 and _SEVERITY_WEIGHT[s] > 0
        ]
        deduction = sum(f.points for f in factors)
        return cls(
            score=max(0, 100 - deduction),
            complexity=min(100, deduction),
            blocker_count=counts[RiskSeverity.BLOCKER],
            high_count=counts[RiskSeverity.HIGH],
            medium_count=counts[RiskSeverity.MEDIUM],
            low_count=counts[RiskSeverity.LOW],
            info_count=counts[RiskSeverity.INFO],
            complexity_factors=factors,
        )
