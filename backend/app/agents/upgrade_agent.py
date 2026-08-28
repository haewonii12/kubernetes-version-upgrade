"""LangGraph 기반 Kubernetes Upgrade Agent (Section 37 Step 4).

Graph Flow::

    START -> collect_cluster -> analyze_cluster -> detect_custom_config ->
    detect_installed_software -> search_rag -> check_compatibility ->
    check_deprecated_api -> analyze_risk -> generate_upgrade_path ->
    generate_upgrade_plan -> END

각 Node는 Collector/Agent 하위 모듈에 위임만 하고 스스로 판단 로직을 갖지
않는다 — 이 파일은 "무엇을 언제 호출하는지"만 담당한다 (책임 분리).
"""

from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.agents.compatibility import evaluate_compatibility, summarize_compatibility
from app.agents.deprecated_api import evaluate_deprecated_apis, summarize_deprecated_apis
from app.agents.planner import build_upgrade_plan, compute_upgrade_path
from app.agents.risk import build_risk_findings
from app.collectors.addon import collect_software_inventory
from app.collectors.certificate import collect_certificate_expirations
from app.collectors.custom_config import CustomConfigCollector
from app.collectors.etcd import EtcdCollector
from app.collectors.kubernetes import KubernetesCollector
from app.collectors.node import NodeCollector, detect_node_inconsistencies
from app.llm.client import LLMClient
from app.mcp.client import MCPClient
from app.models.cluster import ClusterInfo
from app.models.compatibility import CompatibilityResult
from app.models.rag import RAGReference
from app.models.risk import ReadinessScore, RiskFinding
from app.models.upgrade import DeprecatedAPIFinding, UpgradePlan
from app.rag.retriever import RAGRetriever


class AgentState(TypedDict, total=False):
    current_version: str
    target_version: str
    cluster: ClusterInfo
    node_warnings: list[str]
    observed_api_resources: list[dict]
    reference_material: dict[str, list[RAGReference]]
    upgrade_path: list[str]
    compatibility_results: list[CompatibilityResult]
    compatibility_summary: list[CompatibilityResult]
    deprecated_findings: list[DeprecatedAPIFinding]
    deprecated_summary: list[DeprecatedAPIFinding]
    risks: list[RiskFinding]
    readiness: ReadinessScore
    upgrade_plan: UpgradePlan


# LangGraph 노드 이름 -> 사용자에게 보여줄 한국어 진행 메시지 (Section 18 SSE 이벤트에서 재사용).
NODE_PROGRESS_MESSAGES: dict[str, str] = {
    "collect_cluster": "Kubernetes 버전 / Node / Control Plane HA / etcd 정보 수집 중",
    "analyze_cluster": "Node 간 OS/Kernel/Runtime 일관성 분석 중",
    "detect_custom_config": "kube-apiserver 등 Custom Configuration 탐지 중",
    "detect_installed_software": "Namespace 전체 Software Inventory 및 CRD 조사 중",
    "search_rag": "Release Note / kubeadm Upgrade Guide RAG 검색 중",
    "check_compatibility": "Compatibility 분석 중",
    "check_deprecated_api": "Deprecated / Removed API 검사 중",
    "analyze_risk": "Risk 분석 및 업그레이드 준비 복잡도 계산 중",
    "generate_upgrade_path": "Upgrade Path 생성 중",
    "generate_upgrade_plan": "Version별 Upgrade Scenario 생성 중",
}


def build_graph(client: MCPClient, rag: RAGRetriever, llm_client: LLMClient | None = None):
    kubernetes_collector = KubernetesCollector(client)
    node_collector = NodeCollector(client)
    etcd_collector = EtcdCollector(client)
    custom_config_collector = CustomConfigCollector(client)

    def collect_cluster(state: AgentState) -> dict:
        version = kubernetes_collector.collect_kubernetes_version()
        control_plane = kubernetes_collector.collect_control_plane_info()
        worker_count = kubernetes_collector.collect_worker_count()
        nodes = node_collector.collect()
        etcd = etcd_collector.collect()
        cni, cni_version = kubernetes_collector.collect_cni()
        csi_drivers = kubernetes_collector.collect_csi_drivers()
        ingress_controller = kubernetes_collector.collect_ingress_controller()
        crds = kubernetes_collector.collect_crds()
        helm_detected = kubernetes_collector.collect_helm_detected()
        certificate_expirations = collect_certificate_expirations(client)

        cluster = ClusterInfo(
            kubernetes_version=version,
            control_plane=control_plane,
            worker_node_count=worker_count,
            nodes=nodes,
            etcd=etcd,
            cni=cni,
            cni_version=cni_version,
            csi_drivers=csi_drivers,
            ingress_controller=ingress_controller,
            crds=crds,
            helm_detected=helm_detected,
            certificate_expirations=certificate_expirations,
        )
        return {"cluster": cluster, "current_version": version}

    def analyze_cluster(state: AgentState) -> dict:
        warnings = detect_node_inconsistencies(state["cluster"].nodes)
        return {"node_warnings": warnings}

    def detect_custom_config(state: AgentState) -> dict:
        custom_configs = custom_config_collector.collect()
        updated = state["cluster"].model_copy(update={"custom_configs": custom_configs})
        return {"cluster": updated}

    def detect_installed_software(state: AgentState) -> dict:
        inventory = collect_software_inventory(client)
        updated = state["cluster"].model_copy(update={"software_inventory": inventory})
        observed_api_resources = kubernetes_collector.collect_observed_api_resources()
        return {"cluster": updated, "observed_api_resources": observed_api_resources}

    def search_rag(state: AgentState) -> dict:
        # Compatibility/Deprecated API 검사에 필요한 구조화된 근거는 각 전용 노드가
        # RAGRetriever를 직접 호출한다. 이 노드는 Report에 부가로 첨부할 일반
        # 참고자료(Version Skew Policy, kubeadm Upgrade Guide)를 미리 확보한다.
        reference_material = {
            "version_skew_policy": rag.search(
                "kubelet kube-apiserver 버전 skew 정책 순차 업그레이드", doc_type="version_skew_policy"
            ),
            "kubeadm_upgrade_guide": rag.search(
                "kubeadm upgrade drain uncordon 절차", doc_type="kubeadm_upgrade_guide"
            ),
        }
        return {"reference_material": reference_material}

    def check_compatibility(state: AgentState) -> dict:
        upgrade_path = compute_upgrade_path(state["current_version"], state["target_version"])
        results = evaluate_compatibility(state["cluster"], upgrade_path, rag)
        return {"upgrade_path": upgrade_path, "compatibility_results": results}

    def check_deprecated_api(state: AgentState) -> dict:
        findings = evaluate_deprecated_apis(state.get("observed_api_resources", []), state["upgrade_path"], rag)
        return {"deprecated_findings": findings}

    def analyze_risk(state: AgentState) -> dict:
        compatibility_summary = summarize_compatibility(state["compatibility_results"])
        deprecated_summary = summarize_deprecated_apis(state["deprecated_findings"])
        risks = build_risk_findings(
            state["cluster"], state.get("node_warnings", []), compatibility_summary, deprecated_summary
        )
        readiness = ReadinessScore.from_findings(risks)
        return {
            "compatibility_summary": compatibility_summary,
            "deprecated_summary": deprecated_summary,
            "risks": risks,
            "readiness": readiness,
        }

    def generate_upgrade_path(state: AgentState) -> dict:
        # upgrade_path는 check_compatibility 단계에서 이미 계산되었다 (Compatibility가
        # 단계별로 달라지는 판단이라 경로가 먼저 필요했기 때문). 여기서는 Section 37
        # Step4가 요구하는 명시적 Node 순서를 그대로 노출하기 위해 통과시킨다.
        return {"upgrade_path": state["upgrade_path"]}

    def generate_upgrade_plan(state: AgentState) -> dict:
        plan = build_upgrade_plan(
            current_version=state["current_version"],
            target_version=state["target_version"],
            upgrade_path=state["upgrade_path"],
            cluster=state["cluster"],
            compatibility_results=state["compatibility_results"],
            deprecated_findings=state["deprecated_findings"],
            risks=state["risks"],
            rag=rag,
            llm_client=llm_client,
        )
        return {"upgrade_plan": plan}

    graph = StateGraph(AgentState)
    graph.add_node("collect_cluster", collect_cluster)
    graph.add_node("analyze_cluster", analyze_cluster)
    graph.add_node("detect_custom_config", detect_custom_config)
    graph.add_node("detect_installed_software", detect_installed_software)
    graph.add_node("search_rag", search_rag)
    graph.add_node("check_compatibility", check_compatibility)
    graph.add_node("check_deprecated_api", check_deprecated_api)
    graph.add_node("analyze_risk", analyze_risk)
    graph.add_node("generate_upgrade_path", generate_upgrade_path)
    graph.add_node("generate_upgrade_plan", generate_upgrade_plan)

    graph.add_edge(START, "collect_cluster")
    graph.add_edge("collect_cluster", "analyze_cluster")
    graph.add_edge("analyze_cluster", "detect_custom_config")
    graph.add_edge("detect_custom_config", "detect_installed_software")
    graph.add_edge("detect_installed_software", "search_rag")
    graph.add_edge("search_rag", "check_compatibility")
    graph.add_edge("check_compatibility", "check_deprecated_api")
    graph.add_edge("check_deprecated_api", "analyze_risk")
    graph.add_edge("analyze_risk", "generate_upgrade_path")
    graph.add_edge("generate_upgrade_path", "generate_upgrade_plan")
    graph.add_edge("generate_upgrade_plan", END)

    return graph.compile()
