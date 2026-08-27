---
doc_id: fleet-agent-compatibility-matrix
title: Fleet Agent Compatibility Matrix
doc_type: compatibility_matrix
component: fleet-agent
applies_to_k8s: ["1.32", "1.33", "1.34", "1.35", "1.36"]
tags: [fleet-agent, gitops, rancher]
---

fleet-agent는 Fleet 컨트롤 플레인과 동일한 버전(0.6.0)으로 각 관리 대상
클러스터에 배포되는 에이전트로, 독립적인 Kubernetes 지원 범위 문서가 없습니다.
`compatibility-matrix/fleet.md`와 동일하게 Rancher 2.7.x의 인증 범위/EOL 상태를
그대로 물려받습니다.

```yaml
compatibility_matrix:
  component: fleet-agent
  current_version_pattern: "0.6"
  entries:
    - target_kubernetes_minor: "1.32"
      status: INCOMPATIBLE
      reason: "fleet-agent 0.6.0은 Fleet 0.6.0/Rancher 2.7.x와 버전이 묶여 배포되는 에이전트라 독립적인 K8s 지원 범위가 없습니다. Rancher 2.7.x의 인증 범위(1.23~1.25)와 EOL 상태를 물려받습니다 — 근거는 compatibility-matrix/rancher.md 참고."
      recommendation: "Rancher/Fleet을 먼저 업그레이드하세요 — fleet-agent는 Fleet 업그레이드에 종속되어 함께 갱신됩니다."
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

- [Fleet 0.6.0 shipped with Rancher 2.7.3 (rancher/fleet#1507)](https://github.com/rancher/fleet/issues/1507)
- [rag/documents/compatibility-matrix/rancher.md](rancher.md)
