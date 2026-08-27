---
doc_id: envoy-compatibility-matrix
title: Envoy (Proxy) Compatibility Matrix
doc_type: compatibility_matrix
component: envoy
applies_to_k8s: ["1.32", "1.33", "1.34", "1.35", "1.36"]
tags: [envoy, envoy-gateway, data-plane]
---

Envoy 자체는 데이터 플레인 프록시로 Kubernetes API를 직접 호출하지 않기
때문에 독립적인 Kubernetes 버전 호환성 문서를 제공하지 않습니다. 이
클러스터에서 발견된 `distroless-v1.38.0` 빌드는 Envoy Gateway v1.8이 공식
Compatibility Matrix에 명시한 **번들 Envoy Proxy 버전과 정확히 일치**합니다
— 즉 Envoy Gateway 컨트롤 플레인에 의해 배포된 데이터 플레인입니다. 따라서
Kubernetes 버전과의 실질적 호환성은 이를 관리하는
`compatibility-matrix/envoyproxy-gateway.md`의 판정을 그대로 따릅니다.

```yaml
compatibility_matrix:
  component: envoy
  current_version_pattern: "distroless-v1.38"
  entries:
    - target_kubernetes_minor: "1.32"
      status: COMPATIBLE
      reason: "Envoy Gateway v1.8 공식 Compatibility Matrix가 명시한 번들 Envoy 버전이며, 해당 릴리스가 Kubernetes 1.32를 지원 버전으로 명시합니다(envoyproxy-gateway.md 참고)."
    - target_kubernetes_minor: "1.33"
      status: COMPATIBLE
      reason: "동일한 사유(Envoy Gateway v1.8이 1.33을 지원)."
    - target_kubernetes_minor: "1.34"
      status: COMPATIBLE
      reason: "동일한 사유(Envoy Gateway v1.8이 1.34를 지원)."
    - target_kubernetes_minor: "1.35"
      status: COMPATIBLE
      reason: "동일한 사유(Envoy Gateway v1.8이 1.35를 지원)."
    - target_kubernetes_minor: "1.36"
      status: WARNING
      reason: "Envoy Gateway v1.8의 공식 지원 범위(1.32~1.35)에 1.36이 포함되어 있지 않습니다 — Envoy 자체 문제가 아니라 이를 배포하는 Envoy Gateway 컨트롤 플레인의 한계입니다."
      recommendation: "envoyproxy-gateway.md와 동일 — Envoy Gateway를 1.36 지원을 명시하는 릴리스로 먼저 업그레이드하세요."
```

## 출처

- [Compatibility Matrix — Envoy Gateway](https://gateway.envoyproxy.io/news/releases/matrix/)
- [rag/documents/compatibility-matrix/envoyproxy-gateway.md](envoyproxy-gateway.md)
