---
doc_id: ingress-nginx-compatibility-matrix
title: ingress-nginx Compatibility Matrix
doc_type: compatibility_matrix
component: ingress-nginx
applies_to_k8s: ["1.32", "1.33", "1.34", "1.35", "1.36"]
tags: [ingress, ingress-nginx, retired, security]
---

> **가장 중요한 사실**: `kubernetes/ingress-nginx` 프로젝트는 Kubernetes
> Steering Committee와 Security Response Committee의 공식 발표에 따라
> **2026년 3월부로 완전히 은퇴(retired)했습니다** — 더 이상 어떤 버그 수정,
> 보안 패치, 업데이트도 나오지 않습니다. 이는 대상 Kubernetes 버전과 **무관하게**
> 적용되는, 이 컴포넌트에 대한 가장 시급한 이슈입니다.

## ingress-nginx 1.12.x 계열

```yaml
compatibility_matrix:
  component: ingress-nginx
  current_version_pattern: "1.12"
  entries:
    - target_kubernetes_minor: "1.32"
      status: WARNING
      reason: "ingress-nginx 1.12.x 공식 Support Versions 표 기준 Kubernetes 1.32까지가 테스트된 마지막 버전입니다. 다만 프로젝트 자체가 2026-03 은퇴(retired)했기 때문에 버전 호환 여부와 무관하게 더 이상 보안 패치가 나오지 않습니다."
      recommendation: "Kubernetes 버전과 무관하게 Gateway API 또는 다른 유지보수 중인 Ingress Controller로 마이그레이션을 최우선으로 계획하세요."
    - target_kubernetes_minor: "1.33"
      status: WARNING
      reason: "ingress-nginx 1.12.x 공식 Support Versions 표에 1.33 이상은 포함되어 있지 않습니다(테스트 최상단이 1.32). 프로젝트가 2026-03 은퇴했으므로 향후에도 검증될 계획이 없습니다."
      recommendation: "Gateway API 또는 다른 유지보수 중인 Ingress Controller로 마이그레이션하세요."
    - target_kubernetes_minor: "1.34"
      status: WARNING
      reason: "ingress-nginx 1.12.x 공식 지원 범위(최대 1.32) 밖이며, 프로젝트가 은퇴하여 향후 검증도 없습니다."
      recommendation: "Gateway API 또는 다른 유지보수 중인 Ingress Controller로 마이그레이션하세요."
    - target_kubernetes_minor: "1.35"
      status: WARNING
      reason: "ingress-nginx 1.12.x 공식 지원 범위(최대 1.32) 밖이며, 프로젝트가 은퇴하여 향후 검증도 없습니다."
      recommendation: "Gateway API 또는 다른 유지보수 중인 Ingress Controller로 마이그레이션하세요."
    - target_kubernetes_minor: "1.36"
      status: WARNING
      reason: "ingress-nginx 1.12.x 공식 지원 범위(최대 1.32) 밖이며, 프로젝트가 은퇴하여 향후 검증도 없습니다."
      recommendation: "Gateway API 또는 다른 유지보수 중인 Ingress Controller로 마이그레이션하세요."
```

## ingress-nginx 1.11.x 계열

공식 README Support Versions 표 기준, 1.11.0~1.11.8 전체가 Kubernetes
**1.26~1.30**만 테스트 대상으로 명시되어 있습니다(1.12.x의 상한 1.32보다도
더 낮음). 1.32~1.36 전 구간이 공식 테스트 범위 밖이며, 여기에 더해 프로젝트
자체가 2026-03 은퇴한 것은 1.12.x와 동일하게 적용됩니다.

```yaml
compatibility_matrix:
  component: ingress-nginx
  current_version_pattern: "1.11"
  entries:
    - target_kubernetes_minor: "1.32"
      status: WARNING
      reason: "ingress-nginx 1.11.x 공식 Support Versions 표 기준 테스트 대상은 Kubernetes 1.26~1.30까지이며 1.32는 포함되지 않습니다. 프로젝트 자체도 2026-03 은퇴(retired)했습니다."
      recommendation: "Kubernetes 버전과 무관하게 Gateway API 또는 다른 유지보수 중인 Ingress Controller로 마이그레이션을 최우선으로 계획하세요."
    - target_kubernetes_minor: "1.33"
      status: WARNING
      reason: "ingress-nginx 1.11.x 공식 Support Versions 표 기준 테스트 대상은 Kubernetes 1.26~1.30까지이며 이 목표 버전은 포함되지 않습니다. 프로젝트 자체도 2026-03 은퇴(retired)해 향후 검증 계획이 없습니다."
      recommendation: "Gateway API 또는 다른 유지보수 중인 Ingress Controller로 마이그레이션하세요."
    - target_kubernetes_minor: "1.34"
      status: WARNING
      reason: "ingress-nginx 1.11.x 공식 Support Versions 표 기준 테스트 대상은 Kubernetes 1.26~1.30까지이며 이 목표 버전은 포함되지 않습니다. 프로젝트 자체도 2026-03 은퇴(retired)해 향후 검증 계획이 없습니다."
      recommendation: "Gateway API 또는 다른 유지보수 중인 Ingress Controller로 마이그레이션하세요."
    - target_kubernetes_minor: "1.35"
      status: WARNING
      reason: "ingress-nginx 1.11.x 공식 Support Versions 표 기준 테스트 대상은 Kubernetes 1.26~1.30까지이며 이 목표 버전은 포함되지 않습니다. 프로젝트 자체도 2026-03 은퇴(retired)해 향후 검증 계획이 없습니다."
      recommendation: "Gateway API 또는 다른 유지보수 중인 Ingress Controller로 마이그레이션하세요."
    - target_kubernetes_minor: "1.36"
      status: WARNING
      reason: "ingress-nginx 1.11.x 공식 Support Versions 표 기준 테스트 대상은 Kubernetes 1.26~1.30까지이며 이 목표 버전은 포함되지 않습니다. 프로젝트 자체도 2026-03 은퇴(retired)해 향후 검증 계획이 없습니다."
      recommendation: "Gateway API 또는 다른 유지보수 중인 Ingress Controller로 마이그레이션하세요."
```

## 프로젝트 은퇴(Retirement) 상세

- **발표**: 2026-01-29, Kubernetes Steering Committee + Security Response Committee 공동 성명.
- **은퇴 시점**: 2026년 3월. 이후 버그 수정/보안 패치/업데이트가 전혀 없습니다.
- **사유**: "1~2명이 여가 시간에 유지보수해온" 극심한 메인테이너 부족과, 누적된
  기술 부채·설계상 보안 결함이 더 이상 유지보수를 지속할 수 없는 수준이라는 것.
- **공식 권고**: Gateway API 또는 타사(third-party) Ingress Controller로 마이그레이션.
  "은퇴 이후에도 ingress-nginx를 계속 사용하는 것은 사용자를 공격에 노출시키는
  것"이라고 명시.
- Kubernetes Ingress API 자체(리소스 스펙)는 계속 존재하나 feature-frozen 상태이며,
  영향을 받는 것은 `kubernetes/ingress-nginx` 컨트롤러 구현체입니다. F5/NGINX Inc.의
  별도 `nginxinc/kubernetes-ingress` 컨트롤러는 이 은퇴와 무관합니다.

## 출처

- [Ingress NGINX: Statement from the Kubernetes Steering and Security Response Committees](https://www.kubernetes.io/blog/2026/01/29/ingress-nginx-statement/)
- [ingress-nginx README — Support Versions table](https://github.com/kubernetes/ingress-nginx/blob/main/README.md)
