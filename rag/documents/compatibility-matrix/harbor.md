---
doc_id: harbor-compatibility-matrix
title: Harbor Compatibility Matrix
doc_type: compatibility_matrix
component: harbor
applies_to_k8s: ["1.32", "1.33", "1.34", "1.35", "1.36"]
tags: [harbor, registry]
---

> **중요**: Harbor는 core/jobservice/portal/registry/trivy 등 여러 마이크로서비스로
> 구성되며 보통 공식 Helm 차트(`goharbor/harbor-helm`)로 배포됩니다. 이 차트의
> Prerequisites는 **Kubernetes 1.20+** 만 명시하고 있고, 릴리스별 상한 버전이나
> 세부 테스트 매트릭스는 공개 문서에서 확인하지 못했습니다. 반면 **Harbor 2.8
> 자체의 제품 지원(EOS)은 2024-06-04에 이미 종료**되었습니다 — 이 문서의
> 판정은 K8s 버전 호환성이 아니라 **이 버전 자체가 2년 넘게 보안 패치를
> 받지 못하고 있다는 사실**을 주된 근거로 삼습니다.

```yaml
compatibility_matrix:
  component: harbor
  current_version_pattern: "2.8"
  entries:
    - target_kubernetes_minor: "1.32"
      status: WARNING
      reason: "Harbor 2.8 자체의 공식 지원(EOS)이 2024-06-04에 종료되어, 대상 Kubernetes 버전과 무관하게 이미 2년 이상 보안 패치를 받지 못하고 있습니다. Helm 차트의 Kubernetes 요구사항(1.20+)만 보면 기술적으로 동작할 수 있으나 이는 무의미합니다."
      recommendation: "Kubernetes 업그레이드와 별개로, 현재 지원 중인 Harbor 릴리스(2.15.x 계열 등, goharbor.io 확인)로 우선 업그레이드하세요."
    - target_kubernetes_minor: "1.33"
      status: WARNING
      reason: "Harbor 2.8 자체의 공식 지원(EOS)이 2024-06-04에 종료되어, 대상 Kubernetes 버전과 무관하게 이미 2년 이상 보안 패치를 받지 못하고 있습니다. Helm 차트의 Kubernetes 요구사항(1.20+)만 보면 기술적으로 동작할 수 있으나 이는 무의미합니다."
      recommendation: "Kubernetes 업그레이드와 별개로, 현재 지원 중인 Harbor 릴리스(2.15.x 계열 등, goharbor.io 확인)로 우선 업그레이드하세요."
    - target_kubernetes_minor: "1.34"
      status: WARNING
      reason: "Harbor 2.8 자체의 공식 지원(EOS)이 2024-06-04에 종료되어, 대상 Kubernetes 버전과 무관하게 이미 2년 이상 보안 패치를 받지 못하고 있습니다. Helm 차트의 Kubernetes 요구사항(1.20+)만 보면 기술적으로 동작할 수 있으나 이는 무의미합니다."
      recommendation: "Kubernetes 업그레이드와 별개로, 현재 지원 중인 Harbor 릴리스(2.15.x 계열 등, goharbor.io 확인)로 우선 업그레이드하세요."
    - target_kubernetes_minor: "1.35"
      status: WARNING
      reason: "Harbor 2.8 자체의 공식 지원(EOS)이 2024-06-04에 종료되어, 대상 Kubernetes 버전과 무관하게 이미 2년 이상 보안 패치를 받지 못하고 있습니다. Helm 차트의 Kubernetes 요구사항(1.20+)만 보면 기술적으로 동작할 수 있으나 이는 무의미합니다."
      recommendation: "Kubernetes 업그레이드와 별개로, 현재 지원 중인 Harbor 릴리스(2.15.x 계열 등, goharbor.io 확인)로 우선 업그레이드하세요."
    - target_kubernetes_minor: "1.36"
      status: WARNING
      reason: "Harbor 2.8 자체의 공식 지원(EOS)이 2024-06-04에 종료되어, 대상 Kubernetes 버전과 무관하게 이미 2년 이상 보안 패치를 받지 못하고 있습니다. Helm 차트의 Kubernetes 요구사항(1.20+)만 보면 기술적으로 동작할 수 있으나 이는 무의미합니다."
      recommendation: "Kubernetes 업그레이드와 별개로, 현재 지원 중인 Harbor 릴리스(2.15.x 계열 등, goharbor.io 확인)로 우선 업그레이드하세요."
```

## 출처

- [Harbor Helm Chart README — Prerequisites (Kubernetes cluster 1.20+)](https://github.com/goharbor/harbor-helm/blob/main/README.md)
- [Harbor Compatibility List](https://goharbor.io/docs/2.8.0/install-config/harbor-compatibility-list/) — "Harbor 2.8.0 is no longer supported."
- [Harbor — endoflife.date](https://endoflife.date/harbor) — 2.8 release 2023-04-13, support ended 2024-06-04, 최신 패치 2.8.6
