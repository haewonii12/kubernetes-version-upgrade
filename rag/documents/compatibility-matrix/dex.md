---
doc_id: dex-compatibility-matrix
title: Dex (dexidp/dex) Compatibility Matrix
doc_type: compatibility_matrix
component: dex
applies_to_k8s: ["1.32", "1.33", "1.34", "1.35", "1.36"]
tags: [dex, oidc, argocd]
---

> Dex는 ArgoCD가 내장 OIDC Provider로 사용하는 별도 컴포넌트입니다. Dex 자체는
> Kubernetes API에 직접 의존하지 않는 OIDC/OAuth2 서버라 Kubernetes 버전과의
> 기술적 결합이 없습니다 — 이 문서 저장소의 `prometheus.md`, `postgresql.md`와
> 동일한 성격입니다.
>
> Dex는 CNCF 인큐베이팅 프로젝트로 커뮤니티가 운영하며, 공식적으로 명시된
> LTS/EOL 정책(예: "N-2 버전까지 보안 패치 제공" 같은 문서화된 보증)을 찾지
> 못했습니다 — 통상적인 커뮤니티 프로젝트 관례상 최신 릴리스만 활발히
> 관리됩니다. 여기서 실제로 의미 있는 위험은 K8s 버전이 아니라 **최신
> 릴리스와의 격차**입니다. 이 클러스터가 쓰는 **2.38.0** 대비, 이 문서 작성
> 시점(2026-08) 최신 릴리스는 **v2.45.0**(2026-02-23)으로 7개 이상의 minor
> 릴리스 뒤처져 있습니다.

```yaml
compatibility_matrix:
  component: dex
  current_version_pattern: "2.38"
  entries:
    - target_kubernetes_minor: "1.32"
      status: WARNING
      reason: "Dex는 명시적 LTS/EOL 정책이 확인되지 않는 커뮤니티 프로젝트이며, 현재 버전(2.38.0)이 최신(v2.45.0) 대비 7개 이상 minor 릴리스 뒤처져 있어 그 사이의 보안 수정을 놓쳤을 가능성이 있습니다. Kubernetes 버전과의 직접적 결합은 없습니다."
      recommendation: "Kubernetes 업그레이드와 별개로 Dex를 최신 안정 버전으로 우선 업그레이드하세요(dexidp/dex GitHub Releases 확인)."
    - target_kubernetes_minor: "1.33"
      status: WARNING
      reason: "Dex는 명시적 LTS/EOL 정책이 확인되지 않는 커뮤니티 프로젝트이며, 현재 버전(2.38.0)이 최신(v2.45.0) 대비 7개 이상 minor 릴리스 뒤처져 있어 그 사이의 보안 수정을 놓쳤을 가능성이 있습니다. Kubernetes 버전과의 직접적 결합은 없습니다."
      recommendation: "Dex를 최신 버전으로 업그레이드하세요."
    - target_kubernetes_minor: "1.34"
      status: WARNING
      reason: "Dex는 명시적 LTS/EOL 정책이 확인되지 않는 커뮤니티 프로젝트이며, 현재 버전(2.38.0)이 최신(v2.45.0) 대비 7개 이상 minor 릴리스 뒤처져 있어 그 사이의 보안 수정을 놓쳤을 가능성이 있습니다. Kubernetes 버전과의 직접적 결합은 없습니다."
      recommendation: "Dex를 최신 버전으로 업그레이드하세요."
    - target_kubernetes_minor: "1.35"
      status: WARNING
      reason: "Dex는 명시적 LTS/EOL 정책이 확인되지 않는 커뮤니티 프로젝트이며, 현재 버전(2.38.0)이 최신(v2.45.0) 대비 7개 이상 minor 릴리스 뒤처져 있어 그 사이의 보안 수정을 놓쳤을 가능성이 있습니다. Kubernetes 버전과의 직접적 결합은 없습니다."
      recommendation: "Dex를 최신 버전으로 업그레이드하세요."
    - target_kubernetes_minor: "1.36"
      status: WARNING
      reason: "Dex는 명시적 LTS/EOL 정책이 확인되지 않는 커뮤니티 프로젝트이며, 현재 버전(2.38.0)이 최신(v2.45.0) 대비 7개 이상 minor 릴리스 뒤처져 있어 그 사이의 보안 수정을 놓쳤을 가능성이 있습니다. Kubernetes 버전과의 직접적 결합은 없습니다."
      recommendation: "Dex를 최신 버전으로 업그레이드하세요."
```

## 출처

- [dexidp/dex Releases (GitHub)](https://github.com/dexidp/dex/releases) — 최신 v2.45.0 (2026-02-23) 확인
- [Dex — Release Process](https://dexidp.io/docs/development/releases/)
- [rag/documents/compatibility-matrix/postgresql.md](postgresql.md) — 동일한 "K8s API 비결합 + patch 지연" 판단 패턴 참고
