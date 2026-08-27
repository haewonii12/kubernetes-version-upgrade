---
doc_id: gitjob-compatibility-matrix
title: gitjob (Fleet 의존성) Compatibility Matrix
doc_type: compatibility_matrix
component: gitjob
applies_to_k8s: ["1.32", "1.33", "1.34", "1.35", "1.36"]
tags: [gitjob, fleet, rancher]
---

gitjob은 Fleet이 내부적으로 사용하는 git polling 컨트롤러로, 독립 프로젝트로
배포되지 않고 Fleet 릴리스에 종속되어 함께 버전이 올라갑니다(0.1.37은 Fleet
0.6.0/Rancher 2.7.x 배포판에 번들된 버전). 별도의 공식 Kubernetes 지원 범위
문서를 찾지 못했고, `compatibility-matrix/fleet.md`와 동일하게 Rancher 2.7.x의
인증 범위/EOL 상태를 물려받는 것으로 처리했습니다.

```yaml
compatibility_matrix:
  component: gitjob
  current_version_pattern: "0.1"
  entries:
    - target_kubernetes_minor: "1.32"
      status: INCOMPATIBLE
      reason: "gitjob 0.1.37은 Fleet 0.6.0/Rancher 2.7.x에 번들된 의존성으로 독립적인 K8s 지원 범위 문서가 없습니다. Rancher 2.7.x의 인증 범위(1.23~1.25)와 EOL 상태를 물려받습니다 — 근거는 compatibility-matrix/rancher.md 참고."
      recommendation: "Rancher/Fleet을 먼저 업그레이드하세요 — gitjob은 Fleet 업그레이드에 종속되어 함께 갱신됩니다."
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
