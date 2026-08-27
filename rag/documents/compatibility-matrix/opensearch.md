---
doc_id: opensearch-compatibility-matrix
title: OpenSearch Compatibility Matrix
doc_type: compatibility_matrix
component: opensearch
applies_to_k8s: ["1.32", "1.33", "1.34", "1.35", "1.36"]
tags: [opensearch, search, logging]
---

> OpenSearch는 Kubernetes API를 직접 호출하지 않는 검색/분석 엔진이라
> Kubernetes 버전과의 기술적 결합이 없습니다 — `prometheus.md`,
> `postgresql.md`와 동일한 성격입니다.
>
> 다른 컴포넌트들과 달리 이 컴포넌트는 **버전이 뒤처지지 않았습니다**.
> OpenSearch 공식 유지보수 정책(opensearch.org/releases)상 "현재 major
> 버전은 다음 major가 유지보수에 들어가거나 1년이 지날 때까지" 지원되는데,
> 이 클러스터가 쓰는 **3.8.0**은 이 문서 작성 시점(2026-08) 기준 OpenSearch
> 3.x 릴리스 트레인의 **최신에 가까운 현재 버전**입니다(3.7이 2026-07,
> 3.8.0이 뒤이어 릴리스됨). 별도 조치가 필요하지 않습니다.

```yaml
compatibility_matrix:
  component: opensearch
  current_version_pattern: "3.8"
  entries:
    - target_kubernetes_minor: "1.32"
      status: COMPATIBLE
      reason: "OpenSearch는 Kubernetes API와 직접 결합되지 않으며, 현재 버전(3.8.0)은 2026-08 기준 활발히 유지보수 중인 최신 릴리스 트레인에 속합니다."
    - target_kubernetes_minor: "1.33"
      status: COMPATIBLE
      reason: "1.32와 동일합니다."
    - target_kubernetes_minor: "1.34"
      status: COMPATIBLE
      reason: "1.32와 동일합니다."
    - target_kubernetes_minor: "1.35"
      status: COMPATIBLE
      reason: "1.32와 동일합니다."
    - target_kubernetes_minor: "1.36"
      status: COMPATIBLE
      reason: "1.32와 동일합니다. 다만 향후 목표 버전 도달 시점이 늦어질수록 OpenSearch 3.8.0도 그만큼 오래된 버전이 되므로, 업그레이드 시점에 최신 patch 여부를 재확인하세요."
```

## 출처

- [Release Schedule and Maintenance Policy — OpenSearch](https://opensearch.org/releases/)
- [OpenSearch — endoflife.date](https://endoflife.date/opensearch)
- [opensearch-project/OpenSearch 3.8.0 Release Notes](https://github.com/opensearch-project/opensearch-build/blob/main/release-notes/opensearch-release-notes-3.8.0.md)
- [rag/documents/compatibility-matrix/prometheus.md](prometheus.md) — 동일한 "K8s API 비결합" 판단 패턴 참고
