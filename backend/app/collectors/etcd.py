"""etcd Topology/Member/Health 수집 (Section 6).

주의: 실제 ``etcdctl endpoint health`` 는 Pod exec 이 필요해 Read-Only(get/list/watch)
RBAC 범위를 벗어난다 (Section 30). 따라서 이 Collector는 etcd mirror pod(정적 Pod)
스펙과 Pod 상태(Ready condition)만으로 topology/member/probable-health 를
간접적으로 추론하고, Upgrade Plan의 Pre-Check 단계에서 운영자가 직접
``etcdctl endpoint health`` 를 실행하도록 명시적으로 안내한다.
"""

from __future__ import annotations

from app.collectors._utils import container_args, extract_flag, pod_ready
from app.mcp.client import MCPClient
from app.models.cluster import EtcdInfo, EtcdMember, EtcdTopology

_ETCD_PREFIX = "etcd-"
_APISERVER_PREFIX = "kube-apiserver-"


class EtcdCollector:
    def __init__(self, client: MCPClient) -> None:
        self._client = client

    def collect(self) -> EtcdInfo:
        pods = self._client.get_pods(namespace="kube-system")
        etcd_pods = [p for p in pods if p["metadata"]["name"].startswith(_ETCD_PREFIX)]
        apiserver_pods = [p for p in pods if p["metadata"]["name"].startswith(_APISERVER_PREFIX)]

        if not etcd_pods:
            # etcd 정적 Pod가 하나도 없으면 external etcd(클러스터 밖) 이거나 조회 불가 상태.
            return EtcdInfo(topology=EtcdTopology.UNKNOWN, members=[], all_healthy=False, backup_supported=False)

        members: list[EtcdMember] = []
        for pod in etcd_pods:
            name = pod["metadata"]["name"]
            node = pod["spec"].get("nodeName") or name.removeprefix(_ETCD_PREFIX)
            args = container_args(pod, "etcd")
            candidates = (extract_flag(args, "--listen-client-urls") or "").split(",")
            non_loopback = [c for c in candidates if c and "127.0.0.1" not in c]
            endpoint = (non_loopback or candidates or ["unknown"])[0]
            image = pod["spec"]["containers"][0]["image"]
            version = image.rsplit(":", 1)[-1].lstrip("v") if ":" in image else None
            members.append(EtcdMember(name=node, endpoint=endpoint, healthy=pod_ready(pod), version=version))

        # stacked: control-plane 노드마다 etcd 정적 Pod가 kube-apiserver 정적 Pod와 1:1로 존재.
        topology = EtcdTopology.STACKED if len(etcd_pods) == len(apiserver_pods) and apiserver_pods else EtcdTopology.EXTERNAL

        return EtcdInfo(
            topology=topology,
            members=members,
            version=members[0].version if members else None,
            all_healthy=all(m.healthy for m in members),
            backup_supported=True,
        )
