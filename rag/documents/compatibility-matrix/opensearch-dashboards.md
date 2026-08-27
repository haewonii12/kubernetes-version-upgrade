---
doc_id: opensearch-dashboards-compatibility-matrix
title: OpenSearch Dashboards Compatibility Matrix
doc_type: compatibility_matrix
component: opensearch-dashboards
applies_to_k8s: ["1.32", "1.33", "1.34", "1.35", "1.36"]
tags: [opensearch, opensearch-dashboards, logging]
---

> OpenSearch Dashboards는 OpenSearch 코어와 동일한 버전 번호로 함께 릴리스되는
> 시각화 UI입니다(`opensearch.org` 릴리스 정책상 두 프로젝트는 버전 번호를
> 맞춰 동시 릴리스). Kubernetes API를 직접 호출하지 않으므로 Kubernetes
> 버전과의 기술적 결합이 없고, 지원 상태 판단은 `compatibility-matrix/opensearch.md`와
> 동일합니다 — 이 클러스터가 쓰는 **3.8.0**은 OpenSearch 코어 3.8.0과 짝을
> 이루는 현재 버전입니다.

```yaml
compatibility_matrix:
  component: opensearch-dashboards
  current_version_pattern: "3.8"
  entries:
    - target_kubernetes_minor: "1.32"
      status: COMPATIBLE
      reason: "OpenSearch Dashboards는 Kubernetes API와 직접 결합되지 않으며, OpenSearch 코어와 동일한 버전(3.8.0)으로 2026-08 기준 활발히 유지보수 중인 릴리스 트레인에 속합니다."
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
      reason: "1.32와 동일합니다. OpenSearch 코어와 버전을 항상 맞춰 업그레이드하세요."
```

## 출처

- [Release Schedule and Maintenance Policy — OpenSearch](https://opensearch.org/releases/)
- [rag/documents/compatibility-matrix/opensearch.md](opensearch.md) — 동일 릴리스 트레인, 동일 판단 근거
