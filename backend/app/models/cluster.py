from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class NodeRole(str, Enum):
    CONTROL_PLANE = "control-plane"
    WORKER = "worker"


class NodeInfo(BaseModel):
    """단일 Node에서 수집한 OS/Kernel/Runtime 사실 정보. 판단은 포함하지 않는다."""

    name: str
    role: NodeRole
    os_name: str | None = None
    os_version: str | None = None
    kernel_version: str | None = None
    architecture: str | None = None
    cgroup_version: str | None = None
    container_runtime: str | None = None
    container_runtime_version: str | None = None
    kubelet_version: str | None = None
    ready: bool = True


class EtcdTopology(str, Enum):
    STACKED = "stacked"
    EXTERNAL = "external"
    UNKNOWN = "unknown"


class EtcdMember(BaseModel):
    name: str
    endpoint: str
    healthy: bool
    version: str | None = None


class EtcdInfo(BaseModel):
    topology: EtcdTopology
    members: list[EtcdMember] = Field(default_factory=list)
    version: str | None = None
    all_healthy: bool = False
    backup_supported: bool = True


class ControlPlaneInfo(BaseModel):
    node_count: int
    is_ha: bool
    node_names: list[str] = Field(default_factory=list)


class CustomConfigArg(BaseModel):
    """kubeadm이 생성하는 기본 manifest에는 없는, 사용자가 직접 추가한 설정."""

    component: str  # kube-apiserver | kube-controller-manager | kube-scheduler | etcd
    node: str
    flag: str
    value: str | None = None
    manifest_path: str


class SoftwareComponent(BaseModel):
    """Namespace 전체를 스캔해 이미지 태그 등으로 추론한 설치 소프트웨어."""

    name: str
    version: str | None
    namespace: str
    workload_kind: str
    workload_name: str
    image: str
    source: str = "image-tag-inference"  # image-tag-inference | helm-release | crd
    confidence: str = "high"  # high | medium | low


class CRDInfo(BaseModel):
    name: str
    group: str
    inferred_owner: str | None = None


class ClusterInfo(BaseModel):
    kubernetes_version: str
    control_plane: ControlPlaneInfo
    worker_node_count: int
    nodes: list[NodeInfo] = Field(default_factory=list)
    etcd: EtcdInfo
    cni: str | None = None
    cni_version: str | None = None
    csi_drivers: list[str] = Field(default_factory=list)
    ingress_controller: str | None = None
    custom_configs: list[CustomConfigArg] = Field(default_factory=list)
    software_inventory: list[SoftwareComponent] = Field(default_factory=list)
    crds: list[CRDInfo] = Field(default_factory=list)
    feature_gates: dict[str, bool] = Field(default_factory=dict)
    helm_detected: bool = False
