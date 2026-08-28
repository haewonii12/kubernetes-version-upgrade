---
doc_id: envoyproxy-gateway-compatibility-matrix
title: Envoy Gateway Compatibility Matrix
doc_type: compatibility_matrix
component: envoyproxy-gateway
applies_to_k8s: ["1.32", "1.33", "1.34", "1.35", "1.36"]
tags: [gateway-api, envoy, envoy-gateway]
---

Envoy Gateway(github.com/envoyproxy/gateway)는 공식 문서에 릴리스별 지원
Kubernetes 버전 / 번들 Envoy Proxy 버전 / Gateway API 버전을 명시한
Compatibility Matrix를 제공합니다. v1.8 행을 직접 확인한 결과는 다음과
같습니다: Envoy Proxy `distroless-v1.38.0`, Gateway API `v1.5.1`, 지원
Kubernetes 버전 **1.32~1.35**, EOL **2026-11-08**.

```yaml
compatibility_matrix:
  component: envoyproxy-gateway
  current_version_pattern: "1.8"
  entries:
    - target_kubernetes_minor: "1.32"
      status: COMPATIBLE
      reason: "Envoy Gateway 공식 Compatibility Matrix에 v1.8이 Kubernetes 1.32를 지원 버전으로 명시하고 있습니다."
    - target_kubernetes_minor: "1.33"
      status: COMPATIBLE
      reason: "Envoy Gateway 공식 Compatibility Matrix에 v1.8이 Kubernetes 1.33을 지원 버전으로 명시하고 있습니다(v1.8 지원 범위: 1.32~1.35)."
    - target_kubernetes_minor: "1.34"
      status: COMPATIBLE
      reason: "Envoy Gateway 공식 Compatibility Matrix에 v1.8이 Kubernetes 1.34를 지원 버전으로 명시하고 있습니다(v1.8 지원 범위: 1.32~1.35)."
    - target_kubernetes_minor: "1.35"
      status: COMPATIBLE
      reason: "Envoy Gateway 공식 Compatibility Matrix에 v1.8이 Kubernetes 1.35를 지원 버전으로 명시하고 있습니다(v1.8 지원 범위: 1.32~1.35). 다만 Envoy Gateway v1.8 자체의 EOL이 2026-11-08로 멀지 않았습니다."
      recommendation: "v1.8 EOL(2026-11-08) 전에 다음 마이너 릴리스로 업그레이드 계획을 세우세요."
    - target_kubernetes_minor: "1.36"
      status: WARNING
      reason: "Envoy Gateway 공식 Compatibility Matrix에 v1.8의 지원 버전은 1.32~1.35까지만 명시되어 있고 1.36은 포함되어 있지 않습니다(미검증 상태)."
      recommendation: "Kubernetes 1.36으로 업그레이드하기 전, 1.36을 지원 버전으로 명시하는 이후 Envoy Gateway 릴리스로 먼저 업그레이드하세요."
```

## 출처

- [Compatibility Matrix — Envoy Gateway](https://gateway.envoyproxy.io/news/releases/matrix/) (v1.8 행 직접 확인)
- [Announcing Envoy Gateway v1.8](https://gateway.envoyproxy.io/news/releases/v1.8/)
