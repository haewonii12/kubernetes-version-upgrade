---
doc_id: version-skew-policy
title: Kubernetes Version Skew Policy
doc_type: version_skew_policy
component: kubernetes
applies_to_k8s: ["1.32", "1.33", "1.34", "1.35", "1.36"]
tags: [version-skew, kubeadm]
---

> 공식 Kubernetes Version Skew Policy(kubernetes.io/releases/version-skew-policy)
> 기준으로 작성된 문서입니다.

## 기본 원칙

- **minor version을 건너뛰어 업그레이드하지 않는다.** 1.32 → 1.36 로 바로 가지
  않고 1.32 → 1.33 → 1.34 → 1.35 → 1.36 순서로 한 단계씩 진행한다.
- kube-apiserver는 클러스터 내에서 서로 다른 minor 버전이 최대 1개 차이까지만
  공존 가능하다 (HA 구성에서 순차 업그레이드 도중 발생하는 일시적 상태).
- **kubelet은 kube-apiserver보다 최신 버전일 수 없으며, 최대 3개 minor 낮은
  버전까지 지원된다** (예: kube-apiserver 1.36이면 kubelet 1.36/1.35/1.34/1.33
  모두 지원). 단 1.25 이전 버전 조합에서는 최대 2개 minor까지만 허용되었다.
  Worker Node 업그레이드를 너무 오래 미루지 않는다.
- **kube-controller-manager, kube-scheduler, cloud-controller-manager는
  kube-apiserver와 동일하거나 최대 1개 minor 낮은 버전이어야 한다** (예:
  kube-apiserver 1.36이면 1.36/1.35만 지원).
- **kube-proxy는 kube-apiserver보다 최대 3개 minor 낮은 버전까지 지원된다**
  (kubelet과 동일한 규칙, 1.25 이전 조합은 최대 2개 minor).
- **kubectl은 kube-apiserver 대비 상하 1개 minor 버전(±1) 범위에서 지원된다**
  (예: kube-apiserver 1.36이면 kubectl 1.37/1.36/1.35 지원).

## Control Plane 순서

HA(다중 Control Plane) 구성에서는 Control Plane 노드를 **동시에** 업그레이드하지
않는다. 한 노드씩 순차적으로 업그레이드하고, 각 단계 후 클러스터 상태를 검증한다.

## 출처

- [Kubernetes Version Skew Policy](https://kubernetes.io/releases/version-skew-policy/)
