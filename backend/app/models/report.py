from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from app.models.cluster import ClusterInfo
from app.models.compatibility import CompatibilityResult
from app.models.upgrade import DeprecatedAPIFinding, UpgradePlan
from app.models.risk import ReadinessScore, RiskFinding


class AnalysisStage(str, Enum):
    CLUSTER_CONNECTION = "CLUSTER_CONNECTION"
    NODE_SCAN = "NODE_SCAN"
    CONTROL_PLANE_HA_SCAN = "CONTROL_PLANE_HA_SCAN"
    ETCD_SCAN = "ETCD_SCAN"
    OS_KERNEL_SCAN = "OS_KERNEL_SCAN"
    CONTAINER_RUNTIME_SCAN = "CONTAINER_RUNTIME_SCAN"
    CGROUP_SCAN = "CGROUP_SCAN"
    CUSTOM_CONFIG_SCAN = "CUSTOM_CONFIG_SCAN"
    NAMESPACE_SCAN = "NAMESPACE_SCAN"
    ADDON_SCAN = "ADDON_SCAN"
    CRD_SCAN = "CRD_SCAN"
    RAG_SEARCH = "RAG_SEARCH"
    COMPATIBILITY_CHECK = "COMPATIBILITY_CHECK"
    DEPRECATED_API_CHECK = "DEPRECATED_API_CHECK"
    RISK_ANALYSIS = "RISK_ANALYSIS"
    UPGRADE_PATH_GENERATION = "UPGRADE_PATH_GENERATION"
    UPGRADE_PLAN_GENERATION = "UPGRADE_PLAN_GENERATION"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AnalysisEvent(BaseModel):
    stage: AnalysisStage
    message: str
    timestamp: datetime
    progress: int


class AnalysisRequest(BaseModel):
    target_kubernetes_version: str
    mock_mode: bool = False


class UpgradeReport(BaseModel):
    analysis_id: str
    created_at: datetime
    cluster: ClusterInfo
    readiness: ReadinessScore
    risks: list[RiskFinding] = Field(default_factory=list)
    upgrade_plan: UpgradePlan
    software_compatibility: list[CompatibilityResult] = Field(default_factory=list)
    deprecated_apis: list[DeprecatedAPIFinding] = Field(default_factory=list)
    # pluto 교차검증을 건너뛴 경우 그 사유 (바이너리 부재 등). None이면 정상 수행됨.
    deprecated_api_pluto_skipped: str | None = None
    # LLM Endpoint/Model이 지정된 경우에만 채워지는 전체 요약 (없으면 None).
    executive_summary: str | None = None
