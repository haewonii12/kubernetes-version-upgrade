---
doc_id: rancher-compatibility-matrix
title: Rancher Compatibility Matrix
doc_type: compatibility_matrix
component: rancher
applies_to_k8s: ["1.32", "1.33", "1.34", "1.35", "1.36"]
tags: [rancher, management-cluster]
---

SUSE의 공식 Rancher Support Matrix(버전별 페이지, `suse.com/suse-rancher/support-matrix/`)와
endoflife.date의 Rancher 라이프사이클 자료를 근거로 작성했습니다.

## Rancher 2.7.4

Rancher v2.7.4의 공식 Support Matrix는 Rancher가 관리(provision/import)하는
다운스트림 클러스터에 대해 **Kubernetes 1.23~1.25**까지만 인증합니다
(RKE2/RKE1/K3s 모두 동일 범위, 호스티드 K8s인 AKS/EKS/GKE도 이 시점 기준 유사한
구버전 상한). 1.32~1.36은 이 인증 범위를 크게(7개 minor 이상) 벗어납니다.

추가로 Rancher 2.7 라인 자체가 이미 **EOL 상태**입니다: Full Support는
2024-05-15에 종료, Limited Support(치명적 보안 패치만)도 2024-11-18에
종료되어 현재는 어떤 형태의 지원도 받지 못합니다.

```yaml
compatibility_matrix:
  component: rancher
  current_version_pattern: "2.7"
  entries:
    - target_kubernetes_minor: "1.32"
      status: INCOMPATIBLE
      reason: "Rancher 2.7.4 공식 Support Matrix의 인증 범위는 Kubernetes 1.23~1.25까지이며, Rancher 2.7 라인 자체도 이미 EOL(Limited Support 종료 2024-11-18)입니다."
      recommendation: "Kubernetes 업그레이드 전에 Rancher를 현재 지원되는 최신 버전(2.7 이후 라인)으로 먼저 업그레이드해야 합니다. Rancher 자체 업그레이드 경로는 SUSE 공식 문서를 따르세요."
    - target_kubernetes_minor: "1.33"
      status: INCOMPATIBLE
      reason: "Rancher 2.7.4 공식 Support Matrix의 인증 범위는 Kubernetes 1.23~1.25까지이며, Rancher 2.7 라인 자체도 이미 EOL(Limited Support 종료 2024-11-18)입니다."
      recommendation: "Kubernetes 업그레이드 전에 Rancher를 현재 지원되는 최신 버전(2.7 이후 라인)으로 먼저 업그레이드해야 합니다. Rancher 자체 업그레이드 경로는 SUSE 공식 문서를 따르세요."
    - target_kubernetes_minor: "1.34"
      status: INCOMPATIBLE
      reason: "Rancher 2.7.4 공식 Support Matrix의 인증 범위는 Kubernetes 1.23~1.25까지이며, Rancher 2.7 라인 자체도 이미 EOL(Limited Support 종료 2024-11-18)입니다."
      recommendation: "Kubernetes 업그레이드 전에 Rancher를 현재 지원되는 최신 버전(2.7 이후 라인)으로 먼저 업그레이드해야 합니다. Rancher 자체 업그레이드 경로는 SUSE 공식 문서를 따르세요."
    - target_kubernetes_minor: "1.35"
      status: INCOMPATIBLE
      reason: "Rancher 2.7.4 공식 Support Matrix의 인증 범위는 Kubernetes 1.23~1.25까지이며, Rancher 2.7 라인 자체도 이미 EOL(Limited Support 종료 2024-11-18)입니다."
      recommendation: "Kubernetes 업그레이드 전에 Rancher를 현재 지원되는 최신 버전(2.7 이후 라인)으로 먼저 업그레이드해야 합니다. Rancher 자체 업그레이드 경로는 SUSE 공식 문서를 따르세요."
    - target_kubernetes_minor: "1.36"
      status: INCOMPATIBLE
      reason: "Rancher 2.7.4 공식 Support Matrix의 인증 범위는 Kubernetes 1.23~1.25까지이며, Rancher 2.7 라인 자체도 이미 EOL(Limited Support 종료 2024-11-18)입니다."
      recommendation: "Kubernetes 업그레이드 전에 Rancher를 현재 지원되는 최신 버전(2.7 이후 라인)으로 먼저 업그레이드해야 합니다. Rancher 자체 업그레이드 경로는 SUSE 공식 문서를 따르세요."
```

## 출처

- [Rancher Manager v2.7.4 — Support matrix (SUSE)](https://www.suse.com/suse-rancher/support-matrix/all-supported-versions/rancher-v2-7-4/)
- [Rancher — endoflife.date](https://endoflife.date/rancher)
