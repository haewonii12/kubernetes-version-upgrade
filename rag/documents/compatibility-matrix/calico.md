---
doc_id: calico-compatibility-matrix
title: Calico Compatibility Matrix
doc_type: compatibility_matrix
component: calico
applies_to_k8s: ["1.32", "1.33", "1.34", "1.35", "1.36"]
tags: [cni, calico]
---

## Calico 3.30.x 계열

Calico 공식 문서(Kubernetes requirements 페이지, 버전별 아카이브)에 명시된
"We test Calico vX.Y against the following Kubernetes versions" 목록을 근거로
작성했습니다.

```yaml
compatibility_matrix:
  component: calico
  current_version_pattern: "3.30"
  entries:
    - target_kubernetes_minor: "1.32"
      status: COMPATIBLE
      reason: "Calico 3.30 공식 문서에 Kubernetes 1.32가 테스트 대상 버전으로 명시되어 있습니다."
    - target_kubernetes_minor: "1.33"
      status: COMPATIBLE
      reason: "Calico 3.30 공식 문서에 Kubernetes 1.33이 테스트 대상 버전으로 명시되어 있습니다."
    - target_kubernetes_minor: "1.34"
      status: COMPATIBLE
      reason: "Calico 3.30 공식 문서에 Kubernetes 1.34가 테스트 대상 버전으로 명시되어 있습니다."
    - target_kubernetes_minor: "1.35"
      status: COMPATIBLE
      reason: "Calico 3.30 공식 문서에 Kubernetes 1.35가 테스트 대상 버전으로 명시되어 있습니다."
    - target_kubernetes_minor: "1.36"
      status: WARNING
      reason: "Calico 3.30 공식 문서의 테스트 대상 버전 목록(1.31~1.35)에 1.36은 포함되어 있지 않습니다. 미검증 상태일 뿐 확인된 비호환 사례는 아닙니다."
      recommendation: "Kubernetes 1.36으로 업그레이드하기 전, 1.34~1.36을 공식 테스트 대상으로 명시한 최신 Calico(3.32 계열 등)로 먼저 업그레이드하는 것을 권장합니다."
```

## 참고 — 최신 Calico(3.32) 기준 테스트 버전

Calico 최신 버전(3.32) 공식 문서는 1.34/1.35/1.36을 테스트 대상으로 명시합니다.
즉 Calico를 3.30에서 최신으로 올리면 1.36 타겟도 공식 테스트 범위에 들어옵니다.

## 출처

- [System requirements (Calico latest)](https://docs.tigera.io/calico/latest/getting-started/kubernetes/requirements)
- [System requirements (Calico v3.30 archive)](https://docs.tigera.io/calico/3.30/getting-started/kubernetes/requirements)
