"""``kubeadm certs check-expiration`` 이 보여주는 인증서 만료 정보 수집.

이 명령은 Control Plane 노드의 ``/etc/kubernetes/pki`` 와 ``/etc/kubernetes/*.conf``
를 직접 읽으므로 node exec 없이는 실행할 수 없고 Read-Only MCP 권한(get/list/watch)
범위를 벗어난다 (Section 30). 대신 API로 노출되는 CA 인증서만 실제 만료일을
채우고(``observable=True``), 나머지 kubeadm 관리 인증서는 이름만 나열해
노드에서 직접 확인하도록 표시한다(``observable=False``).

관측 경로:
* ``kube-system/kube-root-ca.crt`` ConfigMap → cluster CA (``ca``)
* ``kube-system/extension-apiserver-authentication`` ConfigMap → front-proxy CA
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from app.mcp.client import MCPClient
from app.models.cluster import CertExpiry

logger = logging.getLogger(__name__)

# kubeadm certs check-expiration 이 출력하는 표준 인증서 목록. CA가 아닌 leaf 인증서는
# 전부 노드 디스크에만 있어 Read-Only 권한으로는 만료일을 알 수 없다.
_NODE_ONLY_CERTS = [
    "admin.conf",
    "apiserver",
    "apiserver-etcd-client",
    "apiserver-kubelet-client",
    "controller-manager.conf",
    "etcd-healthcheck-client",
    "etcd-peer",
    "etcd-server",
    "front-proxy-client",
    "scheduler.conf",
]
_NODE_ONLY_CAS = ["etcd-ca"]
_NODE_SOURCE = "control-plane 노드에서 `kubeadm certs check-expiration` 실행 필요"


def collect_certificate_expirations(client: MCPClient) -> list[CertExpiry]:
    try:
        cms = client.get_configmaps(namespace="kube-system")
    except Exception as exc:  # noqa: BLE001
        logger.warning("configmap 조회 실패 — 인증서 만료 수집을 건너뜁니다: %s", exc)
        cms = []

    by_name = {c.get("metadata", {}).get("name"): c for c in cms}
    result: list[CertExpiry] = []

    root_pem = (by_name.get("kube-root-ca.crt") or {}).get("data", {}).get("ca.crt")
    result.append(_ca_entry("ca", root_pem, "configmap kube-system/kube-root-ca.crt"))

    fp_pem = (by_name.get("extension-apiserver-authentication") or {}).get("data", {}).get(
        "requestheader-client-ca-file"
    )
    result.append(_ca_entry("front-proxy-ca", fp_pem, "configmap kube-system/extension-apiserver-authentication"))

    for name in _NODE_ONLY_CAS:
        result.append(CertExpiry(name=name, is_certificate_authority=True, observable=False, source=_NODE_SOURCE))
    for name in _NODE_ONLY_CERTS:
        result.append(CertExpiry(name=name, observable=False, source=_NODE_SOURCE))

    return result


def _ca_entry(name: str, pem: str | None, source: str) -> CertExpiry:
    if not pem:
        return CertExpiry(name=name, is_certificate_authority=True, observable=False, source=_NODE_SOURCE)
    try:
        from cryptography import x509

        cert = x509.load_pem_x509_certificate(pem.encode())
        not_after = getattr(cert, "not_valid_after_utc", None) or cert.not_valid_after
        if not_after.tzinfo is None:
            not_after = not_after.replace(tzinfo=UTC)
        return CertExpiry(
            name=name,
            expires=not_after,
            residual_days=(not_after - datetime.now(UTC)).days,
            is_certificate_authority=True,
            observable=True,
            source=source,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("%s PEM 파싱 실패: %s", name, exc)
        return CertExpiry(name=name, is_certificate_authority=True, observable=False, source=_NODE_SOURCE)
