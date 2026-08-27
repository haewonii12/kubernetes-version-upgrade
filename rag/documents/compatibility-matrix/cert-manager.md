---
doc_id: cert-manager-compatibility-matrix
title: cert-manager Compatibility Matrix
doc_type: compatibility_matrix
component: cert-manager
applies_to_k8s: ["1.32", "1.33", "1.34", "1.35", "1.36"]
tags: [cert-manager]
---

> **중요**: cert-manager 공식 Supported Releases 표 기준, **cert-manager 1.17은
> Kubernetes 1.29 → 1.33 범위만 지원**하며 **지원 종료일은 2025-10-07로 이미
> 지났습니다**(오늘 기준 EOL 브랜치). 즉 대상 Kubernetes 버전과 무관하게, 이
> cert-manager 버전 자체가 더 이상 보안 패치를 받지 못하는 상태입니다.

```yaml
compatibility_matrix:
  component: cert-manager
  current_version_pattern: "1.17"
  entries:
    - target_kubernetes_minor: "1.32"
      status: WARNING
      reason: "cert-manager 1.17의 공식 지원 범위(1.29→1.33) 안에는 들지만, 1.17 브랜치는 2025-10-07에 EOL(지원 종료)되어 더 이상 보안 패치를 받지 않습니다."
      recommendation: "현재 지원 중인 cert-manager 릴리스로 업그레이드하세요 (cert-manager.io/docs/releases 참고)."
    - target_kubernetes_minor: "1.33"
      status: WARNING
      reason: "cert-manager 1.17 공식 지원 범위의 상한(1.29→1.33)이지만, 1.17 브랜치는 이미 EOL 상태입니다."
      recommendation: "현재 지원 중인 cert-manager 릴리스로 업그레이드하세요."
    - target_kubernetes_minor: "1.34"
      status: WARNING
      reason: "cert-manager 1.17의 공식 지원 범위(1.29→1.33)를 벗어납니다. 미검증이며, 1.17은 이미 EOL 상태라 향후에도 검증될 계획이 없습니다."
      recommendation: "Kubernetes 1.34 업그레이드 전 cert-manager를 1.34+를 지원하는 최신 릴리스로 먼저 업그레이드하세요."
    - target_kubernetes_minor: "1.35"
      status: WARNING
      reason: "cert-manager 1.17의 공식 지원 범위(1.29→1.33)를 벗어납니다."
      recommendation: "cert-manager를 최신 지원 릴리스로 업그레이드하세요."
    - target_kubernetes_minor: "1.36"
      status: WARNING
      reason: "cert-manager 1.17의 공식 지원 범위(1.29→1.33)를 벗어납니다."
      recommendation: "cert-manager를 최신 지원 릴리스로 업그레이드하세요."
```

## 출처

- [Supported Releases (cert-manager)](https://cert-manager.io/docs/releases/) — 1.17 행: "Feb 03, 2025 | Oct 07, 2025 | 1.29 → 1.33"
- [Release 1.17 Notes](https://cert-manager.io/docs/releases/release-notes/release-notes-1.17/)
