---
doc_id: kube-proxy-compatibility-matrix
title: kube-proxy Compatibility Matrix
doc_type: compatibility_matrix
component: kube-proxy
applies_to_k8s: ["1.32", "1.33", "1.34", "1.35", "1.36"]
tags: [kube-proxy, version-skew]
---

> kube-proxy는 Calico/cert-manager 같은 서드파티 애드온이 아니라 Kubernetes
> 코어 컴포넌트입니다. 별도의 프로젝트 Compatibility Matrix가 존재하지 않고,
> 공식 [Kubernetes Version Skew Policy](https://kubernetes.io/releases/version-skew-policy/)가
> 유일한 근거입니다(`kubeadm-guides/version-skew-policy.md`와 동일 출처).
> 핵심 규칙: **kube-proxy는 kube-apiserver보다 최대 3개 minor 낮은 버전까지
> 지원됩니다.** kubeadm으로 정상적으로 순차 업그레이드하면 kube-proxy도 각
> 단계마다 함께 갱신되므로 이 skew 위반은 보통 발생하지 않습니다 — 아래
> 판정은 "kube-proxy 업그레이드를 건너뛴 채 kube-apiserver만 먼저 올린
> 경우"를 가정한 최악의 시나리오 기준입니다.

## kube-proxy 1.32.x 계열 (mock 클러스터 현재 버전: v1.32.13)

```yaml
compatibility_matrix:
  component: kube-proxy
  current_version_pattern: "1.32"
  entries:
    - target_kubernetes_minor: "1.33"
      status: COMPATIBLE
      reason: "kube-apiserver 대비 skew 1개 minor로, Version Skew Policy 허용 범위(최대 3개) 안입니다."
      recommendation: "정상적인 kubeadm 순차 업그레이드에서는 kube-proxy도 함께 갱신되므로 별도 조치가 보통 불필요합니다."
    - target_kubernetes_minor: "1.34"
      status: COMPATIBLE
      reason: "skew 2개 minor로 허용 범위 안입니다."
    - target_kubernetes_minor: "1.35"
      status: WARNING
      reason: "skew 3개 minor로 Version Skew Policy가 허용하는 최대치에 도달합니다. kube-apiserver를 1.35까지 올리는 동안 kube-proxy 업그레이드를 계속 미뤘다면 이 시점이 마지노선입니다."
      recommendation: "kube-proxy를 kube-apiserver와 같은 minor로 갱신하는 것을 권장합니다(kubeadm 순차 업그레이드를 따르면 자동 반영)."
    - target_kubernetes_minor: "1.36"
      status: INCOMPATIBLE
      reason: "skew 4개 minor로 Version Skew Policy 허용 범위(최대 3개)를 벗어납니다. kube-proxy 1.32.x를 그대로 둔 채 kube-apiserver만 1.36으로 올리는 것은 공식 정책 위반입니다."
      recommendation: "kube-apiserver를 1.36으로 올리기 전에 kube-proxy를 최소 1.33 이상으로 먼저 갱신하세요. 통상적인 kubeadm 순차 업그레이드(1.32→1.33→1.34→1.35→1.36)를 따르면 이 상황 자체가 발생하지 않습니다."
```

## 출처

- [Kubernetes Version Skew Policy](https://kubernetes.io/releases/version-skew-policy/)
- [rag/documents/kubeadm-guides/version-skew-policy.md](../kubeadm-guides/version-skew-policy.md)
