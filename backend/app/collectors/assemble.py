"""ClusterInfo 조립 헬퍼 — ``agent.tools.cluster_tools.ClusterInspectorTool`` 전용.

``agents/upgrade_agent.py`` 의 ``collect_cluster``/``detect_custom_config``/
``detect_installed_software`` 세 클로저가 하는 조립 시퀀스와 동일하다. 그 파일은
폐쇄망 워크플로우 코드이며 테스트가 전혀 없어 리팩터링 위험이 있으므로 건드리지
않고, agi 브랜치의 Tool이 쓸 조립 로직만 이 함수로 별도 추출했다 (~25줄 중복은
의도된 것 — 폐쇄망 워크플로우에 테스트가 생기면 그때 공용화한다).
"""

from __future__ import annotations

from app.collectors.addon import collect_software_inventory
from app.collectors.certificate import collect_certificate_expirations
from app.collectors.custom_config import CustomConfigCollector
from app.collectors.etcd import EtcdCollector
from app.collectors.kubernetes import KubernetesCollector
from app.collectors.node import NodeCollector
from app.mcp.client import MCPClient
from app.models.cluster import ClusterInfo


def collect_full_cluster_info(client: MCPClient) -> ClusterInfo:
    kubernetes_collector = KubernetesCollector(client)
    node_collector = NodeCollector(client)
    etcd_collector = EtcdCollector(client)
    custom_config_collector = CustomConfigCollector(client)

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
    custom_configs = custom_config_collector.collect()
    software_inventory = collect_software_inventory(client)

    return ClusterInfo(
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
        custom_configs=custom_configs,
        software_inventory=software_inventory,
    )
