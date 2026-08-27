---
doc_id: metrics-server-compatibility-matrix
title: metrics-server Compatibility Matrix
doc_type: compatibility_matrix
component: metrics-server
applies_to_k8s: ["1.32", "1.33", "1.34", "1.35", "1.36"]
tags: [metrics-server, autoscaling]
---

> kubernetes-sigs/metrics-server 공식 저장소(README의 Compatibility Matrix)
> 기준으로 작성된 문서입니다. metrics-server는 `metrics.k8s.io/v1beta1` API를
> 통해 HPA/kubectl top에 리소스 메트릭을 제공하며, 이 API 자체는 오랜 기간
> 변경되지 않았습니다.

## metrics-server 0.7.x 계열 (mock 클러스터 현재 버전: v0.7.2)

공식 Compatibility Matrix: 0.6.x는 Kubernetes 1.25+, **0.7.x는 Kubernetes
1.27+**, 0.8.x는 1.31+, 0.9.x는 1.34+를 요구합니다(모두 최소 요구 버전이며,
상한을 명시한 표는 없습니다 — `metrics.k8s.io/v1beta1`이 안정 API이기 때문).
0.7.x가 명시적으로 "1.32~1.36에서 테스트됨"이라고 밝히지는 않지만, 최소
요구 버전(1.27+)을 충족하고 API 자체 변경이 없어 기능적으로는 계속 동작할
것으로 판단됩니다. 다만 0.7.x 이후 1.31+/1.34+ 전용으로 명시된 0.8.x/0.9.x가
나온 것은 최신 커널 cgroup 메트릭 수집 방식 등 새 Kubernetes 기능을 활용하기
위함이므로, 1.32~1.36 구간에서 최신 기능/보안 수정을 온전히 받으려면 최신
릴리스로의 업그레이드가 권장됩니다.

```yaml
compatibility_matrix:
  component: metrics-server
  current_version_pattern: "0.7"
  entries:
    - target_kubernetes_minor: "1.32"
      status: COMPATIBLE
      reason: "공식 Compatibility Matrix 기준 0.7.x의 최소 요구 버전(1.27+)을 충족하며, metrics.k8s.io/v1beta1 API에 변경이 없습니다."
    - target_kubernetes_minor: "1.33"
      status: COMPATIBLE
      reason: "1.32와 동일한 사유입니다."
    - target_kubernetes_minor: "1.34"
      status: WARNING
      reason: "최소 요구 버전은 충족하지만, 0.9.x가 1.34+를 명시적으로 지원 대상으로 삼아 나온 시점입니다. 0.7.x는 이 시점 이후의 신규 기능/수정을 반영하지 않습니다."
      recommendation: "최신 metrics-server(0.8.x 이상)로 업그레이드를 검토하세요."
    - target_kubernetes_minor: "1.35"
      status: WARNING
      reason: "1.34와 동일한 사유입니다. 버전 격차가 더 벌어집니다."
      recommendation: "최신 metrics-server로 업그레이드를 검토하세요."
    - target_kubernetes_minor: "1.36"
      status: WARNING
      reason: "1.35와 동일한 사유입니다. 공식 저장소에서 0.7.x에 대한 명시적 EOL/지원 종료 공지는 확인되지 않았으나, 두 세대 이상 뒤처진 릴리스입니다."
      recommendation: "최신 metrics-server로 업그레이드를 검토하세요."
```

## metrics-server 0.9.x 계열 (실제 클러스터 현재 버전: v0.9.0)

공식 Compatibility Matrix 기준 **0.9.x는 Kubernetes 1.34+를 최소 요구**합니다
(상한 명시 없음). 즉 1.32/1.33을 목표로 하는 경우 0.9.x의 공식 명시 최소
요구 버전보다 낮은 조합입니다 — 다만 이는 프로젝트가 공식 지원/테스트
대상으로 보증하지 않는다는 의미이지, `metrics.k8s.io/v1beta1` API 자체가
바뀐 것은 아니라서 즉시 동작 불가를 뜻하지는 않습니다(실제로 현재 클러스터가
1.32.13인데도 0.9.0이 이미 배포되어 있음). 1.34 이상 목표에서는 공식 요구
버전을 충족하므로 COMPATIBLE로 판정합니다.

```yaml
compatibility_matrix:
  component: metrics-server
  current_version_pattern: "0.9"
  entries:
    - target_kubernetes_minor: "1.32"
      status: WARNING
      reason: "metrics-server 0.9.x의 공식 최소 요구 버전은 Kubernetes 1.34+입니다. 1.32는 이 요구를 충족하지 않는 공식 미지원 조합입니다(단, API 자체 변경은 없어 기능적으로는 동작 중일 수 있음)."
      recommendation: "가능하면 목표 버전(1.34+)에 맞는 조합으로 조정하거나, 공식 지원 범위를 벗어난 상태임을 인지하고 진행하세요."
    - target_kubernetes_minor: "1.33"
      status: WARNING
      reason: "1.32와 동일한 사유입니다 — 0.9.x의 최소 요구 버전(1.34+)에 못 미칩니다."
    - target_kubernetes_minor: "1.34"
      status: COMPATIBLE
      reason: "metrics-server 0.9.x의 공식 최소 요구 버전(1.34+)을 충족합니다."
    - target_kubernetes_minor: "1.35"
      status: COMPATIBLE
      reason: "1.34와 동일한 사유입니다."
    - target_kubernetes_minor: "1.36"
      status: COMPATIBLE
      reason: "1.34와 동일한 사유입니다. 공식 매트릭스에 상한이 명시되어 있지 않습니다."
```

## 출처

- [kubernetes-sigs/metrics-server — Compatibility Matrix](https://github.com/kubernetes-sigs/metrics-server#compatibility-matrix)
- [metrics-server Releases](https://github.com/kubernetes-sigs/metrics-server/releases)
