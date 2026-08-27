---
doc_id: postgresql-compatibility-matrix
title: PostgreSQL Compatibility Matrix
doc_type: compatibility_matrix
component: postgresql
applies_to_k8s: ["1.32", "1.33", "1.34", "1.35", "1.36"]
tags: [postgresql, database]
---

> PostgreSQL은 데이터베이스 서버로, Kubernetes API를 직접 호출하지 않으므로
> (plain Deployment/StatefulSet 또는 Helm 차트로 배포된 경우) **Kubernetes
> 버전과의 직접적인 기술적 결합이 없습니다** — 이 점은 이 저장소의
> `prometheus.md`와 동일한 성격입니다. 만약 CloudNativePG/Zalando
> postgres-operator 같은 Operator로 관리 중이라면 해당 Operator의 지원 K8s
> 버전 범위를 별도로 확인해야 합니다(이 컬렉터는 이미지 이름만으로는 Operator
> 관리 여부를 구분하지 못합니다).
>
> 여기서 실제로 의미 있는 위험은 K8s 버전이 아니라 **PostgreSQL 자체의 patch
> 최신성**입니다. PostgreSQL 15 major 라인은 2027-11-11까지 공식 지원되지만,
> 이 클러스터가 쓰는 **15.3.0은 2023년 5월 릴리스**이고 이 문서 작성 시점
> (2026-08) 최신 patch는 **15.19**입니다 — 즉 3년 넘게, 16개 이상의 patch
> release(그 사이의 모든 정기 보안 수정 포함)를 적용하지 않은 상태입니다.

```yaml
compatibility_matrix:
  component: postgresql
  current_version_pattern: "15"
  entries:
    - target_kubernetes_minor: "1.32"
      status: WARNING
      reason: "PostgreSQL 15 major 라인 자체는 2027-11-11까지 지원되지만, 현재 버전(15.3.0)은 최신 patch(15.19) 대비 3년 이상, 16개 이상의 patch release가 뒤처져 있어 그 사이의 보안 수정이 누락되어 있을 가능성이 높습니다. Kubernetes 버전과의 직접적 결합은 없습니다."
      recommendation: "Kubernetes 업그레이드와 별개로 PostgreSQL을 15.x 최신 patch로 우선 업그레이드하세요(postgresql.org 릴리스 노트 확인)."
    - target_kubernetes_minor: "1.33"
      status: WARNING
      reason: "1.32와 동일한 사유(patch 지연)입니다."
      recommendation: "PostgreSQL을 15.x 최신 patch로 업그레이드하세요."
    - target_kubernetes_minor: "1.34"
      status: WARNING
      reason: "1.32와 동일한 사유입니다."
      recommendation: "PostgreSQL을 15.x 최신 patch로 업그레이드하세요."
    - target_kubernetes_minor: "1.35"
      status: WARNING
      reason: "1.32와 동일한 사유입니다."
      recommendation: "PostgreSQL을 15.x 최신 patch로 업그레이드하세요."
    - target_kubernetes_minor: "1.36"
      status: WARNING
      reason: "1.32와 동일한 사유입니다."
      recommendation: "PostgreSQL을 15.x 최신 patch로 업그레이드하세요."
```

## 출처

- [PostgreSQL — endoflife.date](https://endoflife.date/postgresql) — 15 major EOL 2027-11-11, 최신 patch 15.19(2026-08-10)
- [PostgreSQL Versioning Policy](https://www.postgresql.org/support/versioning/)
- [rag/documents/compatibility-matrix/prometheus.md](prometheus.md) — 동일한 "K8s API 비결합" 판단 패턴 참고
