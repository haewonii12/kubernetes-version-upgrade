---
doc_id: redis-compatibility-matrix
title: Redis Compatibility Matrix
doc_type: compatibility_matrix
component: redis
applies_to_k8s: ["1.32", "1.33", "1.34", "1.35", "1.36"]
tags: [redis, cache, argocd]
---

> Redis는 ArgoCD가 내장 캐시로 사용하는 별도 컴포넌트입니다. Redis 자체는
> Kubernetes API를 직접 호출하지 않는 인메모리 데이터스토어라 Kubernetes
> 버전과의 기술적 결합이 없습니다 — `prometheus.md`, `postgresql.md`와 동일한
> 성격입니다.
>
> 여기서 실제로 의미 있는 위험은 K8s 버전이 아니라 **Redis 자체의 EOL
> 상태**입니다. Redis 공식 릴리스 일정(release schedule) 기준 **Redis 7.0
> 라인은 2024-07-29에 이미 End-of-Life** 처리되어, 더 이상 어떤 보안 패치도
> 받지 않습니다. 이 문서 작성 시점(2026-08) 최신 안정 버전은 **Redis 8.10.x**
> (8.10.1, 2026-08-17)입니다 — 이 클러스터가 쓰는 **7.0.15-alpine**은 EOL된
> major 라인의 patch로, major 버전 자체를 올려야 하는 상황입니다(단순 patch
> 업그레이드로는 해결되지 않음).

```yaml
compatibility_matrix:
  component: redis
  current_version_pattern: "7.0"
  entries:
    - target_kubernetes_minor: "1.32"
      status: WARNING
      reason: "Redis 7.0 라인은 2024-07-29에 공식 EOL 처리되어 더 이상 보안 패치를 받지 않습니다. Kubernetes 버전과의 직접적 결합은 없습니다."
      recommendation: "Kubernetes 업그레이드와 별개로 Redis를 현재 유지보수 중인 major 라인(8.x)으로 업그레이드하세요."
    - target_kubernetes_minor: "1.33"
      status: WARNING
      reason: "Redis 7.0 라인은 2024-07-29에 공식 EOL 처리되어 더 이상 보안 패치를 받지 않습니다. 이 클러스터가 쓰는 7.0.15-alpine은 EOL된 major 라인의 patch로, major 버전 자체를 8.x로 올려야 합니다(단순 patch 업그레이드로는 해결 불가). Kubernetes 버전과의 직접적 결합은 없습니다."
      recommendation: "Redis를 8.x로 업그레이드하세요."
    - target_kubernetes_minor: "1.34"
      status: WARNING
      reason: "Redis 7.0 라인은 2024-07-29에 공식 EOL 처리되어 더 이상 보안 패치를 받지 않습니다. 이 클러스터가 쓰는 7.0.15-alpine은 EOL된 major 라인의 patch로, major 버전 자체를 8.x로 올려야 합니다(단순 patch 업그레이드로는 해결 불가). Kubernetes 버전과의 직접적 결합은 없습니다."
      recommendation: "Redis를 8.x로 업그레이드하세요."
    - target_kubernetes_minor: "1.35"
      status: WARNING
      reason: "Redis 7.0 라인은 2024-07-29에 공식 EOL 처리되어 더 이상 보안 패치를 받지 않습니다. 이 클러스터가 쓰는 7.0.15-alpine은 EOL된 major 라인의 patch로, major 버전 자체를 8.x로 올려야 합니다(단순 patch 업그레이드로는 해결 불가). Kubernetes 버전과의 직접적 결합은 없습니다."
      recommendation: "Redis를 8.x로 업그레이드하세요."
    - target_kubernetes_minor: "1.36"
      status: WARNING
      reason: "Redis 7.0 라인은 2024-07-29에 공식 EOL 처리되어 더 이상 보안 패치를 받지 않습니다. 이 클러스터가 쓰는 7.0.15-alpine은 EOL된 major 라인의 patch로, major 버전 자체를 8.x로 올려야 합니다(단순 patch 업그레이드로는 해결 불가). Kubernetes 버전과의 직접적 결합은 없습니다."
      recommendation: "Redis를 8.x로 업그레이드하세요."
```

## 출처

- [Redis — endoflife.date](https://endoflife.date/redis) — 7.0 EOL 2024-07-29, 최신 8.10.1(2026-08-17) 확인
- [Redis Software Support Policy](https://redis.io/legal/software-support-policy/)
- [rag/documents/compatibility-matrix/postgresql.md](postgresql.md) — 동일한 "K8s API 비결합 + EOL" 판단 패턴 참고
