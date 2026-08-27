"""Namespace 전체 워크로드 이미지 → Software Inventory 추론 (Section 7, 12)."""

from __future__ import annotations

import re

from app.mcp.client import MCPClient
from app.models.cluster import SoftwareComponent

_IMAGE_SOFTWARE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"calico/"), "Calico"),
    (re.compile(r"cilium/cilium"), "Cilium"),
    (re.compile(r"coredns/coredns"), "CoreDNS"),
    (re.compile(r"kube-proxy"), "kube-proxy"),
    (re.compile(r"metrics-server/metrics-server|metrics-server$"), "metrics-server"),
    (re.compile(r"ingress-nginx/controller"), "ingress-nginx"),
    (re.compile(r"jetstack/cert-manager-(controller|webhook|cainjector)"), "cert-manager"),
    (re.compile(r"argoproj/argocd"), "ArgoCD"),
    (re.compile(r"prometheus-operator/prometheus-operator"), "Prometheus Operator"),
    (re.compile(r"prom(etheus)?/prometheus"), "Prometheus"),
    (re.compile(r"kube-state-metrics"), "kube-state-metrics"),
    (re.compile(r"goharbor/"), "Harbor"),
    (re.compile(r"keycloak"), "Keycloak"),
    (re.compile(r"postgres"), "PostgreSQL"),
]

# 위 목록에 없는(=curated pattern에 매칭되지 않는) 이미지의 이름을 그대로 fallback으로
# 쓰면 이런 흔한 단어들만 남아 어떤 소프트웨어인지 알 수 없다. 이럴 때는 상위
# 경로 세그먼트를 붙여 구분한다 (예: "ingress-nginx/controller" -> "ingress-nginx-controller").
_GENERIC_IMAGE_SUFFIXES = {
    "controller", "operator", "manager", "agent", "proxy", "server", "node",
    "exporter", "webhook", "init", "job", "cli", "gateway", "dashboard",
}


def _strip_registry_host(repo: str) -> str:
    """이미지 repo에서 레지스트리 호스트 부분만 제거한다.

    ``docker.io/calico/node`` -> ``calico/node``, ``calico/node`` -> ``calico/node``.
    첫 세그먼트에 ``.``/``:``가 있거나 ``localhost``면 레지스트리 호스트로 간주한다.
    """
    parts = repo.split("/")
    if len(parts) > 1 and (parts[0] == "localhost" or "." in parts[0] or ":" in parts[0]):
        return "/".join(parts[1:])
    return repo

# CRD Group -> 소유 Software (Section 12). 실제 조회는 collectors/kubernetes.py 담당,
# 매핑 테이블만 이곳에 두어 addon 추론 로직과 한곳에서 관리한다 (DRY).
CRD_GROUP_OWNER: dict[str, str] = {
    "projectcalico.org": "Calico",
    "crd.projectcalico.org": "Calico",
    "cert-manager.io": "cert-manager",
    "acme.cert-manager.io": "cert-manager",
    "argoproj.io": "ArgoCD",
    "monitoring.coreos.com": "Prometheus Operator",
    "cilium.io": "Cilium",
    "gateway.networking.k8s.io": "Gateway API",
}


def _split_image(image: str) -> tuple[str, str | None]:
    """이미지 문자열을 (repo, tag)로 나눈다. digest(``@sha256:...``)는 무시한다.

    ``rpartition``으로 "마지막" 콜론을 tag 구분자로 본다 — 태그는 ``/``를
    포함할 수 없으므로, ``host:port/repo:tag`` 형태에서도 안전하게 registry
    포트와 태그를 구별할 수 있다.
    """
    without_digest = image.split("@", 1)[0]
    repo, sep, tag = without_digest.rpartition(":")
    if not sep or "/" in tag:
        return without_digest, None
    return repo, tag


def infer_software_from_image(image: str) -> tuple[str | None, str | None]:
    """(component 이름, 버전) 추론.

    잘 알려진 OSS는 ``_IMAGE_SOFTWARE_PATTERNS``로 보기 좋은 이름을 붙이고,
    목록에 없는 이미지도 절대 건너뛰지 않는다 — Section 7은 "전체 Software
    Inventory"를 요구하므로, 매칭되지 않는다고 조용히 빠뜨리면 (예: OpenSearch,
    Envoy Gateway처럼 curated 목록에 없는 소프트웨어) 실제 클러스터에 설치된
    구성 요소가 통째로 안 보이는 문제가 생긴다. 매칭이 안 되면 이미지 경로에서
    일반화된 이름을 뽑아 항상 뭔가는 반환한다.
    """
    repo, tag = _split_image(image)
    version = tag.lstrip("v") if tag and tag != "latest" else None
    for pattern, name in _IMAGE_SOFTWARE_PATTERNS:
        if pattern.search(repo):
            return name, version
    return _fallback_name_from_repo(repo), version


def _fallback_name_from_repo(repo: str) -> str | None:
    stripped = _strip_registry_host(repo)
    parts = [p for p in stripped.split("/") if p]
    if not parts:
        return repo or None
    last = parts[-1]
    if last.lower() in _GENERIC_IMAGE_SUFFIXES and len(parts) > 1:
        return f"{parts[-2]}-{last}"
    return last


def infer_crd_owner(group: str) -> str | None:
    return CRD_GROUP_OWNER.get(group)


def _iter_workload_containers(items: list[dict], kind: str):
    for item in items:
        namespace = item["metadata"]["namespace"]
        workload_name = item["metadata"]["name"]
        containers = item["spec"]["template"]["spec"].get("containers", [])
        for c in containers:
            yield namespace, workload_name, c.get("image", "")


def collect_software_inventory(client: MCPClient) -> list[SoftwareComponent]:
    """전 Namespace의 Deployment/DaemonSet/StatefulSet 이미지에서 Software Inventory 추론."""
    found: dict[tuple[str, str], SoftwareComponent] = {}

    sources: list[tuple[list[dict], str]] = [
        (client.get_deployments(), "Deployment"),
        (client.get_daemonsets(), "DaemonSet"),
        (client.get_statefulsets(), "StatefulSet"),
    ]
    curated_names = {name for _, name in _IMAGE_SOFTWARE_PATTERNS}

    for items, kind in sources:
        for namespace, workload_name, image in _iter_workload_containers(items, kind):
            if not image:
                continue
            name, version = infer_software_from_image(image)
            if not name:
                continue
            key = (name, namespace)
            if key in found:
                continue
            is_curated = name in curated_names
            found[key] = SoftwareComponent(
                name=name,
                version=version,
                namespace=namespace,
                workload_kind=kind,
                workload_name=workload_name,
                image=image,
                source="image-tag-inference",
                confidence="high" if (is_curated and version) else "medium" if version else "low",
            )
    return list(found.values())
