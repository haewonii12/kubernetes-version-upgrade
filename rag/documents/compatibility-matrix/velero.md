---
doc_id: velero-compatibility-matrix
title: Velero Compatibility Matrix
doc_type: compatibility_matrix
component: velero
applies_to_k8s: ["1.32", "1.33", "1.34", "1.35", "1.36"]
tags: [velero, backup, disaster-recovery]
---

Velero(github.com/vmware-tanzu/velero)는 릴리스별 공식 테스트 Kubernetes
버전을 README/문서에 명시합니다. 1.12.x는 Kubernetes **1.25.7 / 1.26.5 /
1.26.7 / 1.27.3**을 테스트 대상으로 명시했습니다(최소 지원 버전은 1.18).
또한 Velero 공식 지원 정책은 **현재 버전 + 직전 minor(n-1)만** 지원 대상으로
삼습니다 — 2023년에 나온 1.12는 2026년 기준 지원 대상에서 한참 벗어나 있습니다.

```yaml
compatibility_matrix:
  component: velero
  current_version_pattern: "1.12"
  entries:
    - target_kubernetes_minor: "1.32"
      status: WARNING
      reason: "Velero 1.12.x의 공식 테스트 대상 Kubernetes 버전(1.25~1.27)에 1.32는 포함되지 않습니다. 또한 Velero 지원 정책(n-1)상 1.12는 이미 지원 대상에서 벗어나 있습니다."
      recommendation: "클러스터 업그레이드 전 Velero를 현재 지원 대상 최신 버전으로 먼저 업그레이드하세요 — 백업/복원 도구 특성상 구버전으로 방치하면 새 클러스터 버전의 볼륨 스냅샷/CRD 동작과 어긋날 위험이 큽니다."
    - target_kubernetes_minor: "1.33"
      status: WARNING
      reason: "동일한 사유입니다."
      recommendation: "동일합니다."
    - target_kubernetes_minor: "1.34"
      status: WARNING
      reason: "동일한 사유입니다."
      recommendation: "동일합니다."
    - target_kubernetes_minor: "1.35"
      status: WARNING
      reason: "동일한 사유입니다."
      recommendation: "동일합니다."
    - target_kubernetes_minor: "1.36"
      status: WARNING
      reason: "동일한 사유입니다."
      recommendation: "동일합니다."
```

## 출처

- [vmware-tanzu/velero README — Compatibility Matrix](https://github.com/vmware-tanzu/velero/blob/main/README.md)
- [Velero Docs — Support Process (n-1 지원 정책)](https://velero.io/docs/latest/support-process/)
