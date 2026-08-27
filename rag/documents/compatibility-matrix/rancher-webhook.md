---
doc_id: rancher-webhook-compatibility-matrix
title: rancher-webhook Compatibility Matrix
doc_type: compatibility_matrix
component: rancher-webhook
applies_to_k8s: ["1.32", "1.33", "1.34", "1.35", "1.36"]
tags: [rancher-webhook, admission-webhook, rancher]
---

rancher-webhook은 Rancher 배포판에 포함된 admission webhook 컴포넌트로,
특정 Rancher 릴리스와 짝을 이뤄 버전이 매겨집니다(0.3.4는 Rancher 2.7.x 배포
사이클에서 나온 버전 — Rancher v2.7.2부터 모든 다운스트림 클러스터에 기본
설치됨). 독립적인 Kubernetes 지원 범위 문서는 없어, `compatibility-matrix/rancher.md`와
동일하게 Rancher 2.7.x의 인증 범위/EOL 상태를 물려받는 것으로 처리했습니다.

```yaml
compatibility_matrix:
  component: rancher-webhook
  current_version_pattern: "0.3"
  entries:
    - target_kubernetes_minor: "1.32"
      status: INCOMPATIBLE
      reason: "rancher-webhook 0.3.4는 Rancher 2.7.x 배포 사이클에 종속된 컴포넌트로 독립적인 K8s 지원 범위가 없습니다. Rancher 2.7.x의 인증 범위(1.23~1.25)와 EOL 상태를 물려받습니다 — 근거는 compatibility-matrix/rancher.md 참고."
      recommendation: "Rancher를 먼저 업그레이드하세요 — rancher-webhook은 Rancher 업그레이드에 종속되어 함께 갱신됩니다."
    - target_kubernetes_minor: "1.33"
      status: INCOMPATIBLE
      reason: "1.32와 동일한 사유."
      recommendation: "1.32와 동일합니다."
    - target_kubernetes_minor: "1.34"
      status: INCOMPATIBLE
      reason: "1.32와 동일한 사유."
      recommendation: "1.32와 동일합니다."
    - target_kubernetes_minor: "1.35"
      status: INCOMPATIBLE
      reason: "1.32와 동일한 사유."
      recommendation: "1.32와 동일합니다."
    - target_kubernetes_minor: "1.36"
      status: INCOMPATIBLE
      reason: "1.32와 동일한 사유."
      recommendation: "1.32와 동일합니다."
```

## 출처

- [rancher-webhook installed in all downstream clusters since v2.7.2 (search finding)](https://github.com/rancher/rancher/releases/tag/v2.7.7)
- [rag/documents/compatibility-matrix/rancher.md](rancher.md)
