from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class RAGDocumentType(str, Enum):
    RELEASE_NOTE = "release_note"
    CHANGELOG = "changelog"
    DEPRECATED_API_GUIDE = "deprecated_api_guide"
    REMOVED_API_GUIDE = "removed_api_guide"
    VERSION_SKEW_POLICY = "version_skew_policy"
    KUBEADM_UPGRADE_GUIDE = "kubeadm_upgrade_guide"
    FEATURE_GATE_CHANGES = "feature_gate_changes"
    API_MIGRATION_GUIDE = "api_migration_guide"
    COMPATIBILITY_MATRIX = "compatibility_matrix"
    OS_REQUIREMENT = "os_requirement"
    KERNEL_REQUIREMENT = "kernel_requirement"
    CGROUP_REQUIREMENT = "cgroup_requirement"


class RAGDocumentMeta(BaseModel):
    """rag/documents/**의 Markdown 문서 하나에 대한 메타데이터 (frontmatter로부터 파싱)."""

    doc_id: str
    title: str
    doc_type: RAGDocumentType
    component: str | None = None  # "calico" | "containerd" | "kubernetes" | ...
    applies_to_k8s: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    path: str


class RAGReference(BaseModel):
    """모든 판단(compatibility/risk)에 첨부되는 근거. 근거 없이 판단하지 않는다."""

    document: str
    section: str | None = None
    doc_id: str | None = None
    excerpt: str | None = None
    score: float | None = None
