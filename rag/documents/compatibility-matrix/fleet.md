---
doc_id: fleet-compatibility-matrix
title: Fleet (Rancher GitOps) Compatibility Matrix
doc_type: compatibility_matrix
component: fleet
applies_to_k8s: ["1.32", "1.33", "1.34", "1.35", "1.36"]
tags: [fleet, gitops, rancher]
---

Fleet은 독립 제품이 아니라 특정 Rancher 릴리스와 짝을 이뤄 배포되는 GitOps
컴포넌트입니다. Fleet 0.6.0은 Rancher 2.7.3과 함께 출시되었고, 이 클러스터의
Rancher 2.7.4도 같은 Fleet 0.6.x 계열을 번들합니다 — 즉 Fleet 자체의 독립적인
Kubernetes 지원 범위 문서는 없고, `compatibility-matrix/rancher.md`에서 확인한
**Rancher 2.7.x의 인증 범위(Kubernetes 1.23~1.25)와 EOL 상태를 그대로 물려받습니다**.

```yaml
compatibility_matrix:
  component: fleet
  current_version_pattern: "0.6"
  entries:
    - target_kubernetes_minor: "1.32"
      status: INCOMPATIBLE
      reason: "Fleet 0.6.0은 Rancher 2.7.3/2.7.4와 짝을 이루는 번들 컴포넌트로, 독립적인 K8s 지원 범위가 없습니다. Rancher 2.7.x의 인증 범위(1.23~1.25)와 EOL 상태를 그대로 물려받습니다 — 자세한 근거는 compatibility-matrix/rancher.md 참고."
      recommendation: "Rancher를 먼저 업그레이드하세요 — Fleet은 Rancher 업그레이드에 종속되어 함께 갱신됩니다."
    - target_kubernetes_minor: "1.33"
      status: INCOMPATIBLE
      reason: "Fleet 0.6.0은 Rancher 2.7.3/2.7.4와 짝을 이루는 번들 컴포넌트로, 독립적인 K8s 지원 범위가 없습니다. Rancher 2.7.x의 인증 범위(1.23~1.25)와 EOL 상태를 그대로 물려받습니다 — 자세한 근거는 compatibility-matrix/rancher.md 참고."
      recommendation: "Rancher를 먼저 업그레이드하세요 — Fleet은 Rancher 업그레이드에 종속되어 함께 갱신됩니다."
    - target_kubernetes_minor: "1.34"
      status: INCOMPATIBLE
      reason: "Fleet 0.6.0은 Rancher 2.7.3/2.7.4와 짝을 이루는 번들 컴포넌트로, 독립적인 K8s 지원 범위가 없습니다. Rancher 2.7.x의 인증 범위(1.23~1.25)와 EOL 상태를 그대로 물려받습니다 — 자세한 근거는 compatibility-matrix/rancher.md 참고."
      recommendation: "Rancher를 먼저 업그레이드하세요 — Fleet은 Rancher 업그레이드에 종속되어 함께 갱신됩니다."
    - target_kubernetes_minor: "1.35"
      status: INCOMPATIBLE
      reason: "Fleet 0.6.0은 Rancher 2.7.3/2.7.4와 짝을 이루는 번들 컴포넌트로, 독립적인 K8s 지원 범위가 없습니다. Rancher 2.7.x의 인증 범위(1.23~1.25)와 EOL 상태를 그대로 물려받습니다 — 자세한 근거는 compatibility-matrix/rancher.md 참고."
      recommendation: "Rancher를 먼저 업그레이드하세요 — Fleet은 Rancher 업그레이드에 종속되어 함께 갱신됩니다."
    - target_kubernetes_minor: "1.36"
      status: INCOMPATIBLE
      reason: "Fleet 0.6.0은 Rancher 2.7.3/2.7.4와 짝을 이루는 번들 컴포넌트로, 독립적인 K8s 지원 범위가 없습니다. Rancher 2.7.x의 인증 범위(1.23~1.25)와 EOL 상태를 그대로 물려받습니다 — 자세한 근거는 compatibility-matrix/rancher.md 참고."
      recommendation: "Rancher를 먼저 업그레이드하세요 — Fleet은 Rancher 업그레이드에 종속되어 함께 갱신됩니다."
```

## 출처

- [Fleet 0.6.0 shipped with Rancher 2.7.3 (rancher/fleet#1507)](https://github.com/rancher/fleet/issues/1507)
- [rag/documents/compatibility-matrix/rancher.md](rancher.md)
