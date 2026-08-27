"""Upgrade Path 계산 + Version별 Upgrade Plan 조립 (Section 5, 10, 16, 17)."""

from __future__ import annotations

from app.llm.client import LLMClient
from app.models.cluster import ClusterInfo, NodeRole
from app.models.compatibility import CompatibilityResult
from app.models.rag import RAGReference
from app.models.risk import RiskFinding
from app.models.upgrade import (
    CheckItem,
    DeprecatedAPIFinding,
    NodeUpgradeStep,
    UpgradeCommand,
    UpgradePlan,
    VersionUpgradePhase,
)
from app.rag.retriever import RAGRetriever


def _parse_version(v: str) -> tuple[int, int, int | None]:
    parts = v.split(".")
    major, minor = int(parts[0]), int(parts[1])
    patch = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else None
    return major, minor, patch


def minor_label(version: str) -> str:
    parts = version.split(".")
    return f"{parts[0]}.{parts[1]}"


def compute_upgrade_path(current_version: str, target_version: str) -> list[str]:
    """Section 10: minor version을 건너뛰지 않고 한 단계씩 순차 업그레이드하는 경로를 만든다."""
    cur_major, cur_minor, _ = _parse_version(current_version)
    tgt_major, tgt_minor, tgt_patch = _parse_version(target_version)

    if tgt_major != cur_major or tgt_minor <= cur_minor:
        raise ValueError(
            f"목표 버전({target_version})은 현재 버전({current_version})보다 높은 "
            "minor 버전이어야 하며, major 버전 변경은 지원하지 않습니다."
        )

    path = [current_version]
    for m in range(cur_minor + 1, tgt_minor):
        path.append(f"{cur_major}.{m}.x")
    last = target_version if tgt_patch is not None else f"{tgt_major}.{tgt_minor}.x"
    path.append(last)
    return path


def _summarize_release_notes(
    to_minor: str, release_refs: list[RAGReference], llm_client: LLMClient | None
) -> tuple[str | None, str | None]:
    """(요약 텍스트, 출처) 반환. 출처는 ``"llm"`` 또는 ``"excerpt"``.

    LLM이 설정되어 있고 호출이 성공하면 검색된 여러 chunk를 근거로 자연어
    요약을 생성한다. LLM이 없거나 실패하면(``LLMClient.summarize`` 는 절대
    예외를 던지지 않고 ``None`` 을 반환한다) 지금까지 해온 대로 검색된 문서의
    원문 발췌로 조용히 fallback한다 — 이 fallback 때문에 LLM 설정이 없거나
    틀려도 분석 자체는 항상 끝까지 진행된다.
    """
    if not release_refs:
        return None, None

    if llm_client is not None and llm_client.is_configured:
        context = "\n\n".join(f"[{ref.document} - {ref.section}]\n{ref.excerpt}" for ref in release_refs)
        generated = llm_client.summarize(
            f"위 근거 자료들을 바탕으로 Kubernetes {to_minor}의 주요 변경사항을 2~3문장으로 요약해줘.",
            context,
        )
        if generated:
            return generated, "llm"

    return release_refs[0].excerpt, "excerpt"


def build_upgrade_plan(
    current_version: str,
    target_version: str,
    upgrade_path: list[str],
    cluster: ClusterInfo,
    compatibility_results: list[CompatibilityResult],
    deprecated_findings: list[DeprecatedAPIFinding],
    risks: list[RiskFinding],
    rag: RAGRetriever,
    llm_client: LLMClient | None = None,
) -> UpgradePlan:
    cp_nodes = sorted(cluster.control_plane.node_names)
    worker_nodes = sorted(n.name for n in cluster.nodes if n.role == NodeRole.WORKER)
    custom_components = sorted({c.component for c in cluster.custom_configs})

    phases: list[VersionUpgradePhase] = []
    for i in range(1, len(upgrade_path)):
        from_v = upgrade_path[i - 1]
        to_v = upgrade_path[i]
        to_minor = minor_label(to_v)

        phase_compat = [r for r in compatibility_results if r.target_kubernetes_version == to_minor]
        phase_deprecated = [f for f in deprecated_findings if f.evaluated_at_target_version == to_minor]
        phase_risks = [r for r in risks if r.related_upgrade_step in (None, f"-> {to_minor}")]

        release_refs = rag.search(
            f"Kubernetes {to_minor} 주요 변경사항 deprecated feature gate",
            doc_type="release_note",
            component="kubernetes",
            top_k=3,
        )
        release_summary, release_summary_source = _summarize_release_notes(to_minor, release_refs, llm_client)

        phases.append(
            VersionUpgradePhase(
                phase_number=i,
                from_version=from_v,
                to_version=to_v,
                release_note_summary=release_summary,
                release_note_summary_source=release_summary_source,
                deprecated_apis=phase_deprecated,
                compatibility_results=phase_compat,
                pre_checks=_build_pre_checks(to_minor, custom_components),
                control_plane_steps=_build_control_plane_steps(cp_nodes, to_minor),
                worker_steps=_build_worker_steps(worker_nodes, to_minor),
                post_checks=_build_post_checks(custom_components),
                risks=phase_risks,
                sources=release_refs,
            )
        )

    return UpgradePlan(
        current_version=current_version,
        target_version=target_version,
        upgrade_path=upgrade_path,
        phases=phases,
    )


def _build_pre_checks(to_minor: str, custom_components: list[str]) -> list[CheckItem]:
    items = [
        CheckItem(description="etcd health 확인 (수동: `etcdctl endpoint health` — Read-Only MCP 권한 범위 밖)"),
        CheckItem(
            description="etcd snapshot backup 생성",
            command="etcdctl snapshot save /backup/etcd-snapshot-$(date +%Y%m%d%H%M%S).db",
        ),
        CheckItem(description="모든 Node Ready 상태 확인", command="kubectl get nodes"),
        CheckItem(description="PodDisruptionBudget이 Drain을 막지 않는지 확인", command="kubectl get pdb -A"),
        CheckItem(description=f"Deprecated/Removed API 검사 (Kubernetes {to_minor} 기준)"),
        CheckItem(description=f"Compatibility 검사 (Kubernetes {to_minor} 기준: CNI/CSI/Container Runtime 등)"),
    ]
    if custom_components:
        items.append(
            CheckItem(
                description="kube-apiserver 등 Custom Configuration manifest 백업",
                command="cp -r /etc/kubernetes/manifests /root/manifests-backup-$(date +%Y%m%d%H%M%S)",
            )
        )
    return items


def _build_control_plane_steps(cp_nodes: list[str], to_minor: str) -> list[NodeUpgradeStep]:
    steps = []
    for idx, node in enumerate(cp_nodes, start=1):
        commands = []
        if idx == 1:
            commands.append(UpgradeCommand(description="Upgrade Plan 확인", command="kubeadm upgrade plan", target=node))
            commands.append(
                UpgradeCommand(description="kubeadm 패키지 업그레이드", command=f"dnf install -y kubeadm-{to_minor}*", target=node)
            )
            commands.append(
                UpgradeCommand(description="Control Plane 설정 적용 (첫 번째 노드)", command=f"kubeadm upgrade apply v{to_minor}.0", target=node)
            )
        else:
            commands.append(
                UpgradeCommand(description="kubeadm 패키지 업그레이드", command=f"dnf install -y kubeadm-{to_minor}*", target=node)
            )
            commands.append(
                UpgradeCommand(description="Control Plane 노드 설정 적용", command="kubeadm upgrade node", target=node)
            )
        commands.append(
            UpgradeCommand(
                description="kubelet/kubectl 업그레이드",
                command=f"dnf install -y kubelet-{to_minor}* kubectl-{to_minor}*",
                target=node,
            )
        )
        commands.append(
            UpgradeCommand(description="kubelet 재시작", command="systemctl daemon-reload && systemctl restart kubelet", target=node)
        )
        steps.append(
            NodeUpgradeStep(
                node=node,
                order=idx,
                commands=commands,
                verification=[
                    "kubectl get nodes",
                    f"kubectl -n kube-system get pods -o wide | grep {node}",
                ],
            )
        )
    return steps


def _build_worker_steps(worker_nodes: list[str], to_minor: str) -> list[NodeUpgradeStep]:
    steps = []
    for idx, node in enumerate(worker_nodes, start=1):
        commands = [
            UpgradeCommand(
                description="Node Drain", command=f"kubectl drain {node} --ignore-daemonsets --delete-emptydir-data", target=node
            ),
            UpgradeCommand(description="kubeadm 패키지 업그레이드", command=f"dnf install -y kubeadm-{to_minor}*", target=node),
            UpgradeCommand(description="Node 설정 적용", command="kubeadm upgrade node", target=node),
            UpgradeCommand(
                description="kubelet/kubectl 업그레이드",
                command=f"dnf install -y kubelet-{to_minor}* kubectl-{to_minor}*",
                target=node,
            ),
            UpgradeCommand(description="kubelet 재시작", command="systemctl daemon-reload && systemctl restart kubelet", target=node),
            UpgradeCommand(description="Node Uncordon", command=f"kubectl uncordon {node}", target=node),
        ]
        steps.append(NodeUpgradeStep(node=node, order=idx, commands=commands, verification=[f"kubectl get node {node}"]))
    return steps


def _build_post_checks(custom_components: list[str]) -> list[CheckItem]:
    items = [
        CheckItem(description="kube-apiserver/controller-manager/scheduler/etcd Pod 상태 확인", command="kubectl -n kube-system get pods"),
        CheckItem(description="CoreDNS 상태 확인", command="kubectl -n kube-system get pods -l k8s-app=kube-dns"),
        CheckItem(description="CNI Pod 상태 확인", command="kubectl -n kube-system get pods -l k8s-app=calico-node"),
        CheckItem(description="애플리케이션 Pod 상태 확인 (전체 Namespace)", command="kubectl get pods -A | grep -v Running"),
    ]
    for component in custom_components:
        items.append(
            CheckItem(
                description=f"{component} Custom Configuration 유지 여부 확인",
                command=f"cat /etc/kubernetes/manifests/{component}.yaml",
            )
        )
    return items
