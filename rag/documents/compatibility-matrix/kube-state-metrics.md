---
doc_id: kube-state-metrics-compatibility-matrix
title: kube-state-metrics Compatibility Matrix
doc_type: compatibility_matrix
component: kube-state-metrics
applies_to_k8s: ["1.32", "1.33", "1.34", "1.35", "1.36"]
tags: [kube-state-metrics, monitoring]
---

> kubernetes/kube-state-metrics 공식 저장소 README의 "Compatibility matrix"
> 표를 근거로 작성했습니다. 이 표는 client-go 버전 기준으로 kube-state-metrics
> 릴리스와 Kubernetes 버전을 매핑하며, **공식적으로 최근 5개 릴리스만
> 표에 유지**합니다.

## kube-state-metrics 2.13.x 계열 (mock 클러스터 현재 버전: v2.13.0)

현재 공식 Compatibility Matrix에 남아있는 가장 오래된 행은 kube-state-metrics
v2.16.0(client-go v1.32)이며, **v2.13.0은 이미 표에서 밀려난(더 이상 유지되지
않는) 버전**입니다. 이는 v2.13.0이 1.32~1.36을 대상으로 공식 검증된 적이
없다는 뜻은 아니지만(v2.13.0 출시 당시에는 그 시점의 client-go에 맞춰
테스트되었을 것), 현재 시점 기준으로는 프로젝트가 이 조합을 더 이상 공식
지원 범위로 추적하지 않습니다.

```yaml
compatibility_matrix:
  component: kube-state-metrics
  current_version_pattern: "2.13"
  entries:
    - target_kubernetes_minor: "1.32"
      status: WARNING
      reason: "공식 Compatibility Matrix(README)에 남아있는 최신 5개 릴리스 목록에 v2.13.0이 더 이상 포함되어 있지 않습니다(가장 오래된 유지 행은 v2.16.0/client-go v1.32). 확인된 비호환 사례는 아니지만 공식 추적 대상 밖입니다."
      recommendation: "kube-state-metrics를 v2.16.0 이상으로 업그레이드하는 것을 권장합니다."
    - target_kubernetes_minor: "1.33"
      status: WARNING
      reason: "공식 Compatibility Matrix(README)에 남아있는 최신 5개 릴리스 목록에 v2.13.0이 더 이상 포함되어 있지 않습니다(가장 오래된 유지 행은 v2.16.0/client-go v1.32). 확인된 비호환 사례는 아니지만 공식 추적 대상 밖입니다. 공식 매트릭스 기준 1.33 대상 릴리스는 v2.17.0입니다."
      recommendation: "kube-state-metrics를 v2.17.0 이상으로 업그레이드하는 것을 권장합니다."
    - target_kubernetes_minor: "1.34"
      status: WARNING
      reason: "공식 매트릭스 기준 1.34 대상 릴리스는 v2.18.0입니다. v2.13.0과의 격차가 더 벌어집니다."
      recommendation: "kube-state-metrics를 v2.18.0 이상으로 업그레이드하는 것을 권장합니다."
    - target_kubernetes_minor: "1.35"
      status: WARNING
      reason: "공식 매트릭스 기준 1.35 대상 릴리스는 v2.19.0입니다."
      recommendation: "kube-state-metrics를 v2.19.0 이상으로 업그레이드하는 것을 권장합니다."
    - target_kubernetes_minor: "1.36"
      status: WARNING
      reason: "공식 매트릭스 기준 1.36 대상 릴리스는 v2.20.0입니다. v2.13.0은 이 시점 기준 7개 마이너 릴리스 이상 뒤처집니다."
      recommendation: "kube-state-metrics를 v2.20.0 이상으로 업그레이드하는 것을 권장합니다."
```

## 출처

- [kubernetes/kube-state-metrics — Compatibility matrix](https://github.com/kubernetes/kube-state-metrics#compatibility-matrix)
