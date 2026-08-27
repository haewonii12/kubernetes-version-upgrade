---
doc_id: argocd-compatibility-matrix
title: ArgoCD Compatibility Matrix
doc_type: compatibility_matrix
component: argocd
applies_to_k8s: ["1.32", "1.33", "1.34", "1.35", "1.36"]
tags: [argocd, gitops]
---

> 공식 Argo CD "Tested Kubernetes Versions" 문서를 근거로 작성되었습니다. 출처는
> 문서 하단 참고.

## Argo CD 2.13.x 계열

Argo CD의 release-2.13 브랜치 공식 문서 기준, 2.13 계열이 **테스트된
Kubernetes 버전 범위는 v1.27 ~ v1.30**입니다. 1.32 이상은 이 테스트 범위
밖입니다 — 즉시 동작 불가를 의미하지는 않지만, 프로젝트가 공식적으로 검증한
범위가 아니므로 WARNING으로 판정합니다.

Argo CD는 3.3부터 "최근 4개 minor"를 테스트 범위로 제공하며, 확인된 범위는
다음과 같습니다: 3.3/3.4 → v1.32~v1.35, 3.5 → v1.33~v1.36. 1.32~1.36 전 구간을
커버하려면 Argo CD 3.4 이상(가능하면 3.5)으로 먼저 업그레이드해야 합니다.

```yaml
compatibility_matrix:
  component: argocd
  current_version_pattern: "2.13"
  entries:
    - target_kubernetes_minor: "1.32"
      status: WARNING
      reason: "Argo CD 2.13.x의 공식 테스트 범위는 Kubernetes v1.27~v1.30이며 1.32는 포함되지 않습니다."
      recommendation: "Argo CD 3.4 이상(v1.32~v1.35 테스트됨)으로 업그레이드 후 진행하세요."
    - target_kubernetes_minor: "1.33"
      status: WARNING
      reason: "Argo CD 2.13.x의 공식 테스트 범위는 Kubernetes v1.27~v1.30이며 1.33은 포함되지 않습니다."
      recommendation: "Argo CD 3.4 이상(v1.32~v1.35 테스트됨)으로 업그레이드 후 진행하세요."
    - target_kubernetes_minor: "1.34"
      status: WARNING
      reason: "Argo CD 2.13.x의 공식 테스트 범위는 Kubernetes v1.27~v1.30이며 1.34는 포함되지 않습니다."
      recommendation: "Argo CD 3.4 이상(v1.32~v1.35 테스트됨)으로 업그레이드 후 진행하세요."
    - target_kubernetes_minor: "1.35"
      status: WARNING
      reason: "Argo CD 2.13.x의 공식 테스트 범위는 Kubernetes v1.27~v1.30이며 1.35는 포함되지 않습니다."
      recommendation: "Argo CD 3.4 이상(v1.32~v1.35 테스트됨)으로 업그레이드 후 진행하세요."
    - target_kubernetes_minor: "1.36"
      status: WARNING
      reason: "Argo CD 2.13.x의 공식 테스트 범위는 Kubernetes v1.27~v1.30이며 1.36은 포함되지 않습니다. 확인된 범위 중 1.36을 커버하는 것은 3.5뿐입니다."
      recommendation: "Argo CD 3.5 이상(v1.33~v1.36 테스트됨)으로 업그레이드 후 진행하세요."
```

## Argo CD 2.12.x 계열 (실제 클러스터 버전: v2.12.3)

Argo CD release-2.12 브랜치 공식 문서 기준, 2.12 계열이 **테스트된 Kubernetes
버전 범위는 v1.26 ~ v1.29**입니다 — 2.13(v1.27~v1.30)보다도 한 세대 더
과거 범위이며, 1.32~1.36과는 전 구간 겹치지 않습니다. 또한 Argo CD의 공식
지원 정책(release-process-and-cadence 문서)상 **최근 3개 minor만 패치
대상**이며, 프로젝트는 이미 2.x를 넘어 3.x 계열(3.3~3.5)까지 릴리스된
상태이므로 2.12는 버전 자체가 EOL입니다(신규 CVE 패치를 받지 못함).

```yaml
compatibility_matrix:
  component: argocd
  current_version_pattern: "2.12"
  entries:
    - target_kubernetes_minor: "1.32"
      status: WARNING
      reason: "Argo CD 2.12.x의 공식 테스트 범위는 Kubernetes v1.26~v1.29이며 1.32는 포함되지 않습니다. 버전 자체도 최근 3개 minor 패치 정책 기준 EOL 상태입니다."
      recommendation: "Argo CD 3.4 이상(v1.32~v1.35 테스트됨)으로 업그레이드 후 진행하세요."
    - target_kubernetes_minor: "1.33"
      status: WARNING
      reason: "1.32와 동일한 사유입니다."
      recommendation: "Argo CD 3.4 이상으로 업그레이드 후 진행하세요."
    - target_kubernetes_minor: "1.34"
      status: WARNING
      reason: "1.32와 동일한 사유입니다."
      recommendation: "Argo CD 3.4 이상으로 업그레이드 후 진행하세요."
    - target_kubernetes_minor: "1.35"
      status: WARNING
      reason: "1.32와 동일한 사유입니다."
      recommendation: "Argo CD 3.4 이상(v1.32~v1.35 테스트됨)으로 업그레이드 후 진행하세요."
    - target_kubernetes_minor: "1.36"
      status: WARNING
      reason: "1.32와 동일한 사유입니다. 확인된 범위 중 1.36을 커버하는 것은 3.5뿐입니다."
      recommendation: "Argo CD 3.5 이상(v1.33~v1.36 테스트됨)으로 업그레이드 후 진행하세요."
```

## 출처

- [Argo CD 2.13 — Tested Kubernetes Versions](https://argo-cd.readthedocs.io/en/release-2.13/operator-manual/tested-kubernetes-versions/)
- [Argo CD 2.12 — Tested Kubernetes Versions](https://argo-cd.readthedocs.io/en/release-2.12/operator-manual/tested-kubernetes-versions/)
- [Argo CD (latest) — Tested Kubernetes Versions](https://argo-cd.readthedocs.io/en/stable/operator-manual/tested-kubernetes-versions/)
- [Argo CD — Release Process and Cadence](https://argo-cd.readthedocs.io/en/latest/developer-guide/release-process-and-cadence/)
