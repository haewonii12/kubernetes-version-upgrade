---
doc_id: prometheus-compatibility-matrix
title: Prometheus / Prometheus Operator Compatibility Matrix
doc_type: compatibility_matrix
component: prometheus
applies_to_k8s: ["1.32", "1.33", "1.34", "1.35", "1.36"]
tags: [prometheus, monitoring]
---

> 공식 Prometheus / Prometheus Operator 문서를 근거로 작성되었습니다. 출처는
> 문서 하단 참고.

## Prometheus

Prometheus 프로젝트는 자체적으로 Kubernetes 버전별 공식 호환성 매트릭스를
게시하지 않습니다. kube-apiserver와는 Kubernetes Service Discovery
(`kubernetes_sd_config`)를 통해서만 통신하며, 이 기능은 안정적인 List/Watch
API에 기반해 폭넓은 버전과 동작하는 것이 일반적이지만 프로젝트가 이를
"공식 지원"으로 문서화하지는 않으므로 명시적 보증은 없습니다. 이 문서 저장소의
`release-notes/k8s-1.33.md`에 따르면 core `v1 Endpoints` API가 1.33부터
Deprecated(제거 계획 없음, EndpointSlice 권장) 상태이므로, `role: endpoints`
기반 SD 설정을 쓰는 경우 `role: endpointslice`로 전환을 권장합니다.

```yaml
compatibility_matrix:
  component: prometheus
  current_version_pattern: "2.55"
  entries:
    - target_kubernetes_minor: "1.32"
      status: WARNING
      reason: "Prometheus는 Kubernetes 버전별 공식 호환성 매트릭스를 게시하지 않아 명시적 보증이 없습니다. Service Discovery API 사용 방식상 일반적으로 동작하나 프로젝트 차원의 검증 문서는 없습니다."
      recommendation: "업그레이드 전 scrape target 및 kubernetes_sd_config 동작을 스테이징에서 검증하세요."
    - target_kubernetes_minor: "1.33"
      status: WARNING
      reason: "Prometheus는 Kubernetes 버전별 공식 호환성 매트릭스를 게시하지 않아 명시적 보증이 없습니다(Service Discovery API 사용 방식상 일반적으로 동작하나 프로젝트 차원의 검증 문서는 없음). 추가로 1.33부터 core v1 Endpoints API가 Deprecated 처리되어(release-notes/k8s-1.33.md 참고), role: endpoints SD 설정을 쓰는 경우 장기적으로 role: endpointslice 전환이 필요합니다."
      recommendation: "kubernetes_sd_config의 role을 endpointslice로 전환하는 것을 검토하세요."
    - target_kubernetes_minor: "1.34"
      status: WARNING
      reason: "Prometheus는 Kubernetes 버전별 공식 호환성 매트릭스를 게시하지 않아 명시적 보증이 없습니다. Kubernetes Service Discovery(kubernetes_sd_config)는 안정적인 List/Watch API에 기반해 폭넓은 버전과 동작하는 것이 일반적이나, 프로젝트가 이를 공식 지원으로 문서화하지는 않습니다."
      recommendation: "업그레이드 전 scrape target 및 kubernetes_sd_config 동작을 스테이징에서 검증하세요."
    - target_kubernetes_minor: "1.35"
      status: WARNING
      reason: "Prometheus는 Kubernetes 버전별 공식 호환성 매트릭스를 게시하지 않아 명시적 보증이 없습니다. Kubernetes Service Discovery(kubernetes_sd_config)는 안정적인 List/Watch API에 기반해 폭넓은 버전과 동작하는 것이 일반적이나, 프로젝트가 이를 공식 지원으로 문서화하지는 않습니다."
      recommendation: "업그레이드 전 scrape target 및 kubernetes_sd_config 동작을 스테이징에서 검증하세요."
    - target_kubernetes_minor: "1.36"
      status: WARNING
      reason: "Prometheus는 Kubernetes 버전별 공식 호환성 매트릭스를 게시하지 않아 명시적 보증이 없습니다. Kubernetes Service Discovery(kubernetes_sd_config)는 안정적인 List/Watch API에 기반해 폭넓은 버전과 동작하는 것이 일반적이나, 프로젝트가 이를 공식 지원으로 문서화하지는 않습니다."
      recommendation: "업그레이드 전 scrape target 및 kubernetes_sd_config 동작을 스테이징에서 검증하세요."
```

## Prometheus Operator

공식 Prometheus Operator 호환성 문서는 v0.84.0 이상부터 Kubernetes v1.25.0+
(또는 `CustomResourceValidationExpressions` feature gate 활성화 시 v1.23.0+)를
요구한다고만 명시하며, v0.79.0처럼 그보다 오래된 릴리스에 대한 명시적 상한
버전 정보는 제공하지 않습니다. v0.79.0은 2026년 8월 기준 최신 안정 버전인
v0.93.1 대비 다수 릴리스(약 14개 이상) 뒤처져 있어, 1.32~1.36 구간에 대한
공식 검증 대상에 포함되어 있지 않을 가능성이 높습니다.

```yaml
compatibility_matrix:
  component: prometheus-operator
  current_version_pattern: "0.79"
  entries:
    - target_kubernetes_minor: "1.32"
      status: WARNING
      reason: "Prometheus Operator 0.79.x는 2026-08 기준 최신(v0.93.1) 대비 크게 뒤처진 버전으로, 이후 출시된 Kubernetes 1.32와의 공식 호환성 검증 문서가 없습니다."
      recommendation: "Kubernetes 업그레이드 전 Prometheus Operator를 현재 유지보수 중인 최신 마이너 라인으로 함께 업그레이드하세요."
    - target_kubernetes_minor: "1.33"
      status: WARNING
      reason: "Prometheus Operator 0.79.x는 2026-08 기준 최신(v0.93.1) 대비 약 14개 이상 릴리스 뒤처진 버전이라 0.79.x는 Kubernetes 1.33에 대한 공식 호환성 검증 대상에 포함되어 있지 않습니다."
      recommendation: "Prometheus Operator를 최신 라인으로 업그레이드 후 진행하세요."
    - target_kubernetes_minor: "1.34"
      status: WARNING
      reason: "Prometheus Operator 0.79.x는 2026-08 기준 최신(v0.93.1) 대비 약 14개 이상 릴리스 뒤처진 버전이라 0.79.x는 Kubernetes 1.34에 대한 공식 호환성 검증 대상에 포함되어 있지 않습니다."
      recommendation: "Prometheus Operator를 최신 라인으로 업그레이드 후 진행하세요."
    - target_kubernetes_minor: "1.35"
      status: WARNING
      reason: "Prometheus Operator 0.79.x는 2026-08 기준 최신(v0.93.1) 대비 약 14개 이상 릴리스 뒤처진 버전이라 0.79.x는 Kubernetes 1.35에 대한 공식 호환성 검증 대상에 포함되어 있지 않습니다."
      recommendation: "Prometheus Operator를 최신 라인으로 업그레이드 후 진행하세요."
    - target_kubernetes_minor: "1.36"
      status: WARNING
      reason: "Prometheus Operator 0.79.x는 2026-08 기준 최신(v0.93.1) 대비 약 14개 이상 릴리스 뒤처진 버전이라 0.79.x는 Kubernetes 1.36에 대한 공식 호환성 검증 대상에 포함되어 있지 않습니다."
      recommendation: "Prometheus Operator를 최신 라인으로 업그레이드 후 진행하세요."
```

## 출처

- [Prometheus Operator — Compatibility](https://prometheus-operator.dev/docs/getting-started/compatibility/)
- [Prometheus Operator — Releases (GitHub)](https://github.com/prometheus-operator/prometheus-operator/releases)
- [Kubernetes v1.33 Release Notes (본 저장소, Endpoints Deprecation 근거)](../release-notes/k8s-1.33.md)
