"""Risk 종합 판단 (Section 14).

여기서 다루는 Risk는 두 갈래다:
1. Compatibility/Deprecated API 처럼 RAG 근거가 있는 판단 → 그대로 등급만 매핑.
2. HA/etcd/Custom Config/Node 일관성처럼 클러스터 구조 자체에서 도출되는 판단
   → Kubernetes 운영 Best Practice(순차 업그레이드, snapshot backup 등)에 기반한
   고정 규칙이며, 이는 Compatibility Rule이 아니라 kubeadm/etcd 운영 원칙이므로
   코드에 두어도 Section 9/25가 금지하는 "Hard Coding"에 해당하지 않는다.
"""

from __future__ import annotations

from app.collectors.custom_config import HIGH_ATTENTION_FLAGS
from app.models.cluster import ClusterInfo, EtcdTopology
from app.models.compatibility import CompatibilityResult, CompatibilityStatus
from app.models.risk import RiskFinding, RiskSeverity
from app.models.upgrade import DeprecatedAPIFinding, DeprecatedAPIStatus


def build_risk_findings(
    cluster: ClusterInfo,
    node_warnings: list[str],
    compatibility_results: list[CompatibilityResult],
    deprecated_findings: list[DeprecatedAPIFinding],
) -> list[RiskFinding]:
    findings: list[RiskFinding] = []
    findings.extend(_node_consistency_risks(node_warnings))
    findings.extend(_custom_config_risks(cluster))
    findings.extend(_etcd_risks(cluster))
    findings.extend(_ha_risks(cluster))
    findings.extend(_cgroup_estimate_notice(cluster))
    findings.extend(_compatibility_risks(compatibility_results))
    findings.extend(_deprecated_api_risks(deprecated_findings))
    return findings


def _node_consistency_risks(warnings: list[str]) -> list[RiskFinding]:
    return [
        RiskFinding(
            finding=w,
            severity=RiskSeverity.MEDIUM,
            category="node-consistency",
            reason="Node 간 환경 설정이 다르면 업그레이드 도중 예기치 않은 동작 차이가 발생할 수 있습니다.",
            recommendation="모든 Node의 OS/Kernel/Container Runtime 버전을 동일하게 맞추는 것을 권장합니다.",
        )
        for w in warnings
    ]


def _custom_config_risks(cluster: ClusterInfo) -> list[RiskFinding]:
    by_component: dict[str, set[str]] = {}
    for c in cluster.custom_configs:
        by_component.setdefault(c.component, set()).add(c.flag)

    findings = []
    for component, flags in by_component.items():
        severity = RiskSeverity.HIGH if flags & HIGH_ATTENTION_FLAGS else RiskSeverity.MEDIUM
        findings.append(
            RiskFinding(
                finding=f"{component}에서 kubeadm 기본값 외 사용자 정의 설정이 발견되었습니다: {', '.join(sorted(flags))}",
                severity=severity,
                category="custom-config",
                reason="kubeadm upgrade는 static pod manifest를 재생성할 수 있어 사용자 정의 설정이 유실될 위험이 있습니다.",
                recommendation=(
                    f"Upgrade 후 `kubectl -n kube-system get pod` 및 "
                    f"`cat /etc/kubernetes/manifests/{component}.yaml` 로 설정이 "
                    "그대로 유지되었는지 반드시 확인하세요."
                ),
            )
        )
    return findings


def _etcd_risks(cluster: ClusterInfo) -> list[RiskFinding]:
    etcd = cluster.etcd
    findings: list[RiskFinding] = []
    if etcd.topology == EtcdTopology.UNKNOWN:
        findings.append(
            RiskFinding(
                finding="etcd Topology를 판별하지 못했습니다.",
                severity=RiskSeverity.HIGH,
                category="etcd",
                reason="kube-system Namespace에서 etcd 정적 Pod 정보를 찾을 수 없습니다 (external etcd이거나 조회 실패).",
                recommendation="etcd 구성을 수동으로 확인하세요.",
            )
        )
        return findings

    if not etcd.all_healthy:
        findings.append(
            RiskFinding(
                finding="일부 etcd member가 비정상(Not Ready) 상태입니다.",
                severity=RiskSeverity.HIGH,
                category="etcd",
                reason="etcd가 불안정한 상태에서 Control Plane을 업그레이드하면 클러스터 전체 장애로 이어질 수 있습니다.",
                recommendation="업그레이드 전 모든 etcd member를 Healthy 상태로 복구하세요.",
            )
        )
    else:
        findings.append(
            RiskFinding(
                finding=(
                    f"etcd Topology: {etcd.topology.value}, Member {len(etcd.members)}개 모두 "
                    "Ready 상태입니다."
                ),
                severity=RiskSeverity.LOW,
                category="etcd",
                reason="정상 상태이지만 업그레이드 전 snapshot backup은 별도로 반드시 수행해야 합니다.",
                recommendation="`etcdctl snapshot save`로 업그레이드 시작 전 snapshot을 생성하세요.",
            )
        )
    findings.append(
        RiskFinding(
            finding="etcd endpoint health(`etcdctl endpoint health`)는 Read-Only MCP 권한(get/list/watch)으로 조회할 수 없습니다.",
            severity=RiskSeverity.INFO,
            category="etcd",
            reason="Section 30 RBAC 정책상 Pod exec 권한을 부여하지 않았습니다.",
            recommendation="업그레이드 담당자가 직접 `etcdctl endpoint health`를 실행해 재확인하세요.",
        )
    )
    return findings


def _ha_risks(cluster: ClusterInfo) -> list[RiskFinding]:
    if cluster.control_plane.node_count > 1:
        return [
            RiskFinding(
                finding=(
                    f"HA Control Plane 구성입니다 ({cluster.control_plane.node_count}대). "
                    "반드시 한 번에 한 대씩 순차 업그레이드하세요."
                ),
                severity=RiskSeverity.INFO,
                category="ha",
                reason="Control Plane을 동시에 업그레이드하면 kube-apiserver 버전 skew 정책 위반 및 API 가용성 문제가 발생할 수 있습니다.",
                recommendation="Upgrade Plan의 Control Plane Upgrade 순서를 그대로 따르세요.",
            )
        ]
    return [
        RiskFinding(
            finding="Control Plane이 단일 노드로 구성되어 있습니다.",
            severity=RiskSeverity.MEDIUM,
            category="ha",
            reason="업그레이드 중 유일한 Control Plane이 일시적으로 unavailable 해질 수 있습니다.",
            recommendation="가능하면 HA 구성으로 전환하거나, 유지보수 시간을 명확히 공지하세요.",
        )
    ]


def _cgroup_estimate_notice(cluster: ClusterInfo) -> list[RiskFinding]:
    if not any(n.cgroup_version for n in cluster.nodes):
        return []
    return [
        RiskFinding(
            finding="cgroup 버전은 OS 기본값 기반 추정치입니다.",
            severity=RiskSeverity.INFO,
            category="cgroup",
            reason="get/list/watch 권한만으로는 실제 cgroup 마운트 상태를 확정할 수 없습니다 (Section 30).",
            recommendation="각 노드에서 `stat -fc %T /sys/fs/cgroup` 실행 결과(cgroup2fs=v2, tmpfs=v1)로 재확인하세요.",
        )
    ]


def _compatibility_risks(results: list[CompatibilityResult]) -> list[RiskFinding]:
    severity_map = {
        CompatibilityStatus.INCOMPATIBLE: RiskSeverity.HIGH,
        CompatibilityStatus.WARNING: RiskSeverity.MEDIUM,
        CompatibilityStatus.UNKNOWN: RiskSeverity.LOW,
    }
    findings = []
    for r in results:
        severity = severity_map.get(r.status)
        if severity is None:  # COMPATIBLE
            continue
        findings.append(
            RiskFinding(
                finding=f"{r.component} ({r.current_version or '?'}) — Kubernetes {r.target_kubernetes_version} 기준 {r.status.value}",
                severity=severity,
                category="compatibility",
                reason=r.reason,
                recommendation=r.recommendation or "공식 Compatibility 문서를 참고해 수동으로 검증하세요.",
                sources=r.sources,
                related_upgrade_step=f"-> {r.target_kubernetes_version}",
            )
        )
    return findings


def _deprecated_api_risks(findings_in: list[DeprecatedAPIFinding]) -> list[RiskFinding]:
    severity_map = {
        DeprecatedAPIStatus.UPGRADE_BLOCKER: RiskSeverity.BLOCKER,
        DeprecatedAPIStatus.ACTION_REQUIRED: RiskSeverity.HIGH,
        DeprecatedAPIStatus.UNKNOWN: RiskSeverity.LOW,
    }
    findings = []
    for f in findings_in:
        severity = severity_map.get(f.status)
        if severity is None:  # OK
            continue
        resource_desc = f"{f.namespace + '/' if f.namespace else ''}{f.resource_name}" if f.resource_name else "(cluster-scoped)"
        findings.append(
            RiskFinding(
                finding=f"{f.resource_kind} {resource_desc} ({f.api_version}) — {f.status.value}",
                severity=severity,
                category="deprecated-api",
                reason=(
                    f"이 API는 Kubernetes {f.removed_in_version}에서 제거됩니다."
                    if f.status == DeprecatedAPIStatus.UPGRADE_BLOCKER
                    else f"이 API는 Kubernetes {f.deprecated_in_version}부터 Deprecated 상태입니다."
                    if f.status == DeprecatedAPIStatus.ACTION_REQUIRED
                    else "RAG 문서에서 이 API에 대한 Deprecated/Removed 정보를 찾지 못했습니다."
                ),
                recommendation=(
                    f"{f.replacement_api_version}(으)로 마이그레이션하세요."
                    if f.replacement_api_version
                    else "공식 문서를 참고해 수동으로 검증하세요 (Manual Verification Required)."
                ),
                sources=f.sources,
                related_upgrade_step=f"-> {f.evaluated_at_target_version}" if f.evaluated_at_target_version else None,
            )
        )
    return findings
