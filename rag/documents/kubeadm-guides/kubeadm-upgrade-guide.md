---
doc_id: kubeadm-upgrade-guide
title: kubeadm Upgrade Guide (일반 절차)
doc_type: kubeadm_upgrade_guide
component: kubeadm
applies_to_k8s: ["1.32", "1.33", "1.34", "1.35", "1.36"]
tags: [kubeadm, upgrade-procedure]
---

## Pre Check

- etcd 상태 확인 (`etcdctl endpoint health` 등 — 이 항목은 Read-Only MCP 권한
  범위를 벗어나므로 운영자가 직접 실행해야 한다).
- etcd snapshot backup 수행.
- 모든 Node `Ready` 상태 확인.
- PodDisruptionBudget이 Drain을 막지 않는지 확인.
- Deprecated/Removed API 사용 여부 확인.

## Control Plane 업그레이드 (첫 번째 노드)

```bash
apt-mark unhold kubeadm && \
apt-get update && apt-get install -y kubeadm='<version>-1.1'   # 또는 dnf install kubeadm-<version>
apt-mark hold kubeadm
kubeadm upgrade plan
kubeadm upgrade apply v<version>

kubectl drain <node> --ignore-daemonsets   # Control Plane은 보통 --delete-emptydir-data 없이 진행

apt-mark unhold kubelet kubectl && \
apt-get install -y kubelet='<version>-1.1' kubectl='<version>-1.1'  # 또는 dnf install kubelet-<version> kubectl-<version>
apt-mark hold kubelet kubectl
systemctl daemon-reload
systemctl restart kubelet

kubectl uncordon <node>
```

## Control Plane 업그레이드 (나머지 노드)

```bash
apt-mark unhold kubeadm && apt-get install -y kubeadm='<version>-1.1'
apt-mark hold kubeadm
kubeadm upgrade node

kubectl drain <node> --ignore-daemonsets
apt-mark unhold kubelet kubectl && apt-get install -y kubelet='<version>-1.1' kubectl='<version>-1.1'
apt-mark hold kubelet kubectl
systemctl daemon-reload
systemctl restart kubelet
kubectl uncordon <node>
```

## Worker Node 업그레이드

```bash
kubectl drain <node> --ignore-daemonsets --delete-emptydir-data
apt-mark unhold kubeadm && apt-get install -y kubeadm='<version>-1.1'
apt-mark hold kubeadm
kubeadm upgrade node

apt-mark unhold kubelet kubectl && apt-get install -y kubelet='<version>-1.1' kubectl='<version>-1.1'
apt-mark hold kubelet kubectl
systemctl daemon-reload
systemctl restart kubelet
kubectl uncordon <node>
```

## Post Check

- `kubectl get nodes` 로 모든 Node 버전/Ready 상태 확인.
- kube-apiserver / controller-manager / scheduler / etcd Pod 상태 확인.
- CoreDNS, CNI, CSI Pod 상태 확인.
- 애플리케이션 Pod 정상 여부 확인.
- Custom Configuration(예: `--encryption-provider-config`)이 재생성된 manifest에
  그대로 유지되었는지 확인.

## 출처

- [Upgrading kubeadm clusters](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-upgrade/)
