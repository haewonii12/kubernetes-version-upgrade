"""Cluster 전반(버전/HA/Namespace/CRD/CNI/CSI) 원시 정보 수집.

동일한 kubectl 호출(get_nodes, get_pods 등)이 여러 하위 Collector에서 반복
호출되지 않도록, MCPClient 자체가 내부 캐시를 갖고(Mock은 파일 캐시, Real은
세션 내 캐시) 이 모듈은 그 결과를 조합만 한다 (DRY, Section 3).
"""

from __future__ import annotations

from app.collectors._utils import is_control_plane_node
from app.collectors.addon import infer_crd_owner, infer_software_from_image
from app.mcp.client import MCPClient
from app.models.cluster import ControlPlaneInfo, CRDInfo


class KubernetesCollector:
    def __init__(self, client: MCPClient) -> None:
        self._client = client
        self._nodes: list[dict] | None = None

    def _raw_nodes(self) -> list[dict]:
        if self._nodes is None:
            self._nodes = self._client.get_nodes()
        return self._nodes

    def collect_kubernetes_version(self) -> str:
        version = self._client.get_version()
        git_version = version.get("serverVersion", {}).get("gitVersion") or version.get("gitVersion")
        if git_version:
            return git_version.lstrip("v")
        nodes = self._raw_nodes()
        if nodes:
            return nodes[0]["status"]["nodeInfo"]["kubeletVersion"].lstrip("v")
        return "unknown"

    def collect_control_plane_info(self) -> ControlPlaneInfo:
        cp_nodes = [n for n in self._raw_nodes() if is_control_plane_node(n)]
        names = [n["metadata"]["name"] for n in cp_nodes]
        return ControlPlaneInfo(node_count=len(cp_nodes), is_ha=len(cp_nodes) > 1, node_names=names)

    def collect_worker_count(self) -> int:
        return len([n for n in self._raw_nodes() if not is_control_plane_node(n)])

    def collect_namespaces(self) -> list[str]:
        return self._client.get_namespaces()

    def collect_crds(self) -> list[CRDInfo]:
        result = []
        for c in self._client.get_crds():
            name = c["metadata"]["name"]
            group = c.get("spec", {}).get("group") or (name.split(".", 1)[1] if "." in name else "")
            result.append(CRDInfo(name=name, group=group, inferred_owner=infer_crd_owner(group)))
        return result

    def collect_helm_detected(self) -> bool:
        return len(self._client.get_helm_releases()) > 0

    def collect_cni(self) -> tuple[str | None, str | None]:
        for ds in self._client.get_daemonsets():
            for c in ds["spec"]["template"]["spec"].get("containers", []):
                name, version = infer_software_from_image(c.get("image", ""))
                if name in ("Calico", "Cilium"):
                    return name, version
        return None, None

    def collect_csi_drivers(self) -> list[str]:
        return sorted({sc["provisioner"] for sc in self._client.get_storage_classes() if sc.get("provisioner")})

    def collect_ingress_controller(self) -> str | None:
        """Ingress 리소스 기반 Controller와 Gateway API Controller를 모두 인식한다.

        전통적 Ingress Controller(예: ingress-nginx)와 Gateway API Controller(예:
        Envoy Gateway)는 상호 배타적이지 않고 한 클러스터에 공존할 수 있어(Section
        20), 둘 다 발견되면 하나로 합쳐서 반환한다.
        """
        found: list[str] = []
        for d in self._client.get_deployments():
            for c in d["spec"]["template"]["spec"].get("containers", []):
                name, version = infer_software_from_image(c.get("image", ""))
                if name == "ingress-nginx":
                    found.append(f"{name} {version}" if version else name)
                elif name == "envoyproxy-gateway":
                    found.append(f"Gateway API (Envoy Gateway {version})" if version else "Gateway API (Envoy Gateway)")
        if not found and self._has_gateway_api_crds():
            found.append("Gateway API")
        return " · ".join(dict.fromkeys(found)) or None

    def _has_gateway_api_crds(self) -> bool:
        return any(
            (c.get("spec", {}).get("group") or "") == "gateway.networking.k8s.io" for c in self._client.get_crds()
        )

    # Deprecated/Removed API 검사 대상 수집은 collectors/manifest_scan.py 로 이동했다
    # (라이브 오브젝트 전체 + 미적용 Helm 차트 매니페스트, RAG + pluto 하이브리드 판정).
