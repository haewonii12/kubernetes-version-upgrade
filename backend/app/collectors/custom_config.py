"""kube-apiserver/controller-manager/scheduler/etcd Custom Argument 탐지 (Section 4).

Static Pod manifest(``/etc/kubernetes/manifests/*.yaml``) 파일을 노드에서 직접
읽으려면 node 접근(bash/exec)이 필요해 Read-Only RBAC 범위를 벗어난다. 대신
kubelet이 static pod마다 kube-system Namespace에 생성하는 "mirror pod"의
``spec.containers[0].command``/``args`` 는 static manifest와 동일한 실행 인자를
그대로 노출하므로, ``kubectl get pod`` (get 권한만 필요) 로 동일한 정보를
얻을 수 있다. 이 설계 덕분에 MCP RBAC을 get/list/watch로만 제한해도
Section 4 요구사항을 충족한다.
"""

from __future__ import annotations

from app.collectors._utils import container_args
from app.mcp.client import MCPClient
from app.models.cluster import CustomConfigArg

# kubeadm이 기본으로 생성하는 flag 목록 (kubeadm 버전에 따라 다소 달라질 수 있는
# 일반적인 baseline). 여기에 없는 flag 가 발견되면 "사용자 정의 설정"으로 간주한다.
# 이는 Kubernetes Compatibility 판단이 아니라 kubeadm 도구 자체의 정적 동작이므로
# RAG 대상이 아니라 코드에 상수로 관리한다.
KUBEADM_DEFAULT_FLAGS: dict[str, set[str]] = {
    "kube-apiserver": {
        "--advertise-address", "--allow-privileged", "--authorization-mode",
        "--client-ca-file", "--enable-admission-plugins", "--enable-bootstrap-token-auth",
        "--etcd-cafile", "--etcd-certfile", "--etcd-keyfile", "--etcd-servers",
        "--insecure-port", "--kubelet-client-certificate", "--kubelet-client-key",
        "--kubelet-preferred-address-types", "--proxy-client-cert-file", "--proxy-client-key-file",
        "--requestheader-allowed-names", "--requestheader-client-ca-file",
        "--requestheader-extra-headers-prefix", "--requestheader-group-headers",
        "--requestheader-username-headers", "--secure-port", "--service-account-issuer",
        "--service-account-key-file", "--service-account-signing-key-file",
        "--service-cluster-ip-range", "--tls-cert-file", "--tls-private-key-file",
        "--api-audiences", "--bind-address",
    },
    "kube-controller-manager": {
        "--allocate-node-cidrs", "--authentication-kubeconfig", "--authorization-kubeconfig",
        "--bind-address", "--client-ca-file", "--cluster-cidr", "--cluster-name",
        "--cluster-signing-cert-file", "--cluster-signing-key-file", "--controllers",
        "--kubeconfig", "--leader-elect", "--requestheader-client-ca-file",
        "--root-ca-file", "--service-account-private-key-file", "--service-cluster-ip-range",
        "--use-service-account-credentials",
    },
    "kube-scheduler": {
        "--authentication-kubeconfig", "--authorization-kubeconfig", "--bind-address",
        "--kubeconfig", "--leader-elect",
    },
    "etcd": {
        "--advertise-client-urls", "--cert-file", "--client-cert-auth", "--data-dir",
        "--initial-advertise-peer-urls", "--initial-cluster", "--initial-cluster-state",
        "--key-file", "--listen-client-urls", "--listen-metrics-urls", "--listen-peer-urls",
        "--name", "--peer-cert-file", "--peer-client-cert-auth", "--peer-key-file",
        "--peer-trusted-ca-file", "--snapshot-count", "--trusted-ca-file",
        # kubeadm이 관리하는 etcd 버전이 3.6.0 이상이면 --feature-gates=InitialCorruptCheck=true
        # / --watch-progress-notify-interval=5s 를, 미만이면 --experimental-* 접두사가 붙은
        # 동의어 flag를 자동으로 넣는다 (cmd/kubeadm/app/phases/etcd/local.go getEtcdCommand,
        # release-1.32~1.36 소스로 직접 확인). kubeadm 기본 etcd가 1.34부터 3.5.21-0 →
        # 3.6.5-0으로 바뀌므로(release-notes/k8s-1.34.md 참고) 1.32~1.33은 experimental-*,
        # 1.34~1.36은 feature-gates/watch-progress-notify-interval 쪽이 기본값이다 — 둘 다
        # 넣어 어느 버전에서도 오탐(false positive)이 나지 않게 한다.
        "--feature-gates", "--watch-progress-notify-interval",
        "--experimental-initial-corrupt-check", "--experimental-watch-progress-notify-interval",
    },
}

# 위 4개 etcd flag는 이름만으로 "기본값"이라 단정하면 안 된다 — 특히 --feature-gates는
# 사용자가 다른 feature gate를 켜기 위해 진짜로 커스텀할 수도 있는 범용 flag라, kubeadm이
# 넣는 정확한 값(InitialCorruptCheck=true 등)일 때만 기본값으로 간주하고, 값이 다르면
# 여전히 Custom Configuration으로 잡아야 한다.
_ETCD_VALUE_LOCKED_DEFAULTS: dict[str, str] = {
    "--feature-gates": "InitialCorruptCheck=true",
    "--watch-progress-notify-interval": "5s",
    "--experimental-initial-corrupt-check": "true",
    "--experimental-watch-progress-notify-interval": "5s",
}

# 특히 중요하게 다뤄야 할 flag (Report에서 강조 표시). Section 4 예시 목록.
HIGH_ATTENTION_FLAGS = {
    "--encryption-provider-config",
    "--audit-policy-file",
    "--audit-log-path",
    "--oidc-issuer-url",
    "--oidc-client-id",
    "--authentication-token-webhook-config-file",
    "--service-account-issuer",
}

_COMPONENT_POD_PREFIX = {
    "kube-apiserver": "kube-apiserver-",
    "kube-controller-manager": "kube-controller-manager-",
    "kube-scheduler": "kube-scheduler-",
    "etcd": "etcd-",
}


class CustomConfigCollector:
    def __init__(self, client: MCPClient) -> None:
        self._client = client

    def collect(self) -> list[CustomConfigArg]:
        pods = self._client.get_pods(namespace="kube-system")
        findings: list[CustomConfigArg] = []
        for component, prefix in _COMPONENT_POD_PREFIX.items():
            defaults = KUBEADM_DEFAULT_FLAGS[component]
            for pod in pods:
                name = pod["metadata"]["name"]
                if not name.startswith(prefix):
                    continue
                node = pod["spec"].get("nodeName") or name.removeprefix(prefix)
                for arg in container_args(pod, component):
                    if not arg.startswith("--"):
                        continue
                    flag, _, value = arg.partition("=")
                    if component == "etcd" and flag in _ETCD_VALUE_LOCKED_DEFAULTS:
                        if value == _ETCD_VALUE_LOCKED_DEFAULTS[flag]:
                            continue
                    elif flag in defaults:
                        continue
                    findings.append(
                        CustomConfigArg(
                            component=component,
                            node=node,
                            flag=flag,
                            value=value or None,
                            manifest_path=(
                                f"/etc/kubernetes/manifests/{component}.yaml "
                                f"(mirror pod kube-system/{name} 기준으로 조회)"
                            ),
                        )
                    )
        return findings
