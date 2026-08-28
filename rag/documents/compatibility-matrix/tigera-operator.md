---
doc_id: tigera-operator-compatibility-matrix
title: tigera-operator Compatibility Matrix
doc_type: compatibility_matrix
component: tigera-operator
applies_to_k8s: ["1.32", "1.33", "1.34", "1.35", "1.36"]
tags: [cni, calico, tigera-operator]
---

tigera-operator는 Calico를 설치/관리하는 Operator이며 자체적으로 별도의
Kubernetes 버전 상한을 두지 않고, 설치하는 Calico 버전의 지원 범위를 그대로
따릅니다. tigera-operator 1.38.x 라인(v1.38.16 기준, GitHub Releases로 직접
확인)은 **Calico v3.30.7**을 설치합니다 — 이는 이 리포지토리의
`compatibility-matrix/calico.md`가 다루는 버전과 정확히 일치합니다. 따라서
아래 판정은 그 문서의 Calico 3.30 계열 판정(공식 테스트 범위 1.31~1.35)을
그대로 상속합니다.

```yaml
compatibility_matrix:
  component: tigera-operator
  current_version_pattern: "1.38"
  entries:
    - target_kubernetes_minor: "1.32"
      status: COMPATIBLE
      reason: "tigera-operator 1.38.x가 설치하는 Calico v3.30.7이 Calico 공식 문서상 Kubernetes 1.32를 테스트 대상으로 명시합니다(compatibility-matrix/calico.md 참고)."
    - target_kubernetes_minor: "1.33"
      status: COMPATIBLE
      reason: "tigera-operator 1.38.x가 설치하는 Calico v3.30.7이 Calico 공식 문서상 Kubernetes 1.33을 테스트 대상으로 명시합니다(compatibility-matrix/calico.md 참고)."
    - target_kubernetes_minor: "1.34"
      status: COMPATIBLE
      reason: "tigera-operator 1.38.x가 설치하는 Calico v3.30.7이 Calico 공식 문서상 Kubernetes 1.34를 테스트 대상으로 명시합니다(compatibility-matrix/calico.md 참고)."
    - target_kubernetes_minor: "1.35"
      status: COMPATIBLE
      reason: "tigera-operator 1.38.x가 설치하는 Calico v3.30.7이 Calico 공식 문서상 Kubernetes 1.35를 테스트 대상으로 명시합니다(compatibility-matrix/calico.md 참고)."
    - target_kubernetes_minor: "1.36"
      status: WARNING
      reason: "Calico 3.30 공식 문서의 테스트 대상 버전 목록(1.31~1.35)에 1.36은 포함되어 있지 않습니다. tigera-operator 자체 문제가 아니라 그것이 설치하는 Calico 버전의 한계입니다."
      recommendation: "Kubernetes 1.36으로 업그레이드하기 전에 tigera-operator를 최신 버전(1.34~1.36을 공식 테스트 대상으로 명시하는 Calico 3.32 계열을 설치하는 릴리스)으로 먼저 업그레이드하세요."
```

## 출처

- [tigera/operator Releases](https://github.com/tigera/operator/releases) (v1.38.16이 Calico v3.30.7을 포함함을 직접 확인)
- [rag/documents/compatibility-matrix/calico.md](calico.md)
