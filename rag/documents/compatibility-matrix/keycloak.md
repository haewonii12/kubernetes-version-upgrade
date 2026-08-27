---
doc_id: keycloak-compatibility-matrix
title: Keycloak Compatibility Matrix
doc_type: compatibility_matrix
component: keycloak
applies_to_k8s: ["1.32", "1.33", "1.34", "1.35", "1.36"]
tags: [keycloak, iam]
---

> **중요**: Keycloak(오픈소스 커뮤니티 배포판)은 **최신 major 버전 하나만
> 활성 지원**하는 정책을 씁니다 — 새 major가 나오는 순간 이전 버전은 사실상
> EOL 처리됩니다. **Keycloak 21.1은 2023-07-11(22.0 출시 시점)에 이미
> 지원이 종료**되었으며, 이 문서 작성 시점(2026-08) 기준 **3년 넘게 보안
> 패치를 받지 못한 상태**입니다. Keycloak은 (Operator 없이 plain
> Deployment/StatefulSet으로 배포된 경우) Kubernetes API를 직접 호출하지
> 않으므로 K8s 버전 자체와의 직접적인 기술적 결합은 문서화되어 있지 않습니다
> — 이 판정은 K8s 호환성이 아니라 **제품 자체의 EOL 상태**를 근거로 합니다.
> 만약 Keycloak Operator로 관리 중이라면 Operator의 별도 지원 K8s 버전 범위를
> 추가로 확인하십시오(이 컬렉터는 이미지 이름만으로는 Operator 관리 여부를
> 구분하지 못합니다).

```yaml
compatibility_matrix:
  component: keycloak
  current_version_pattern: "21.1"
  entries:
    - target_kubernetes_minor: "1.32"
      status: WARNING
      reason: "Keycloak 21.1은 2023-07-11에 지원이 종료되어(커뮤니티 배포판은 최신 major만 지원) 3년 넘게 보안 패치를 받지 못했습니다. 대상 Kubernetes 버전과 무관하게 이 자체가 위험입니다."
      recommendation: "Kubernetes 업그레이드와 별개로 현재 지원 중인 최신 Keycloak major 버전으로 우선 업그레이드하세요(keycloak.org 릴리스 페이지 확인)."
    - target_kubernetes_minor: "1.33"
      status: WARNING
      reason: "1.32와 동일한 사유(Keycloak 21.1 EOL)입니다."
      recommendation: "최신 지원 버전으로 먼저 업그레이드하세요."
    - target_kubernetes_minor: "1.34"
      status: WARNING
      reason: "1.32와 동일한 사유입니다."
      recommendation: "최신 지원 버전으로 먼저 업그레이드하세요."
    - target_kubernetes_minor: "1.35"
      status: WARNING
      reason: "1.32와 동일한 사유입니다."
      recommendation: "최신 지원 버전으로 먼저 업그레이드하세요."
    - target_kubernetes_minor: "1.36"
      status: WARNING
      reason: "1.32와 동일한 사유입니다."
      recommendation: "최신 지원 버전으로 먼저 업그레이드하세요."
```

## 출처

- [Keycloak — endoflife.date](https://endoflife.date/keycloak) — 21.1 릴리스 2023-04-19, 지원 종료 2023-07-11(22.0 출시일), 최신 패치 21.1.2
- [Red Hat build of Keycloak Life Cycle and Support Policies](https://access.redhat.com/support/policy/updates/red_hat_build_of_keycloak_notes) — 커뮤니티 배포판은 최신 major만 지원, 상용은 Red Hat build of Keycloak 참고
