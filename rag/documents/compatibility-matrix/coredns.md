---
doc_id: coredns-compatibility-matrix
title: CoreDNS Compatibility Matrix
doc_type: compatibility_matrix
component: coredns
applies_to_k8s: ["1.32", "1.33", "1.34", "1.35", "1.36"]
tags: [dns, coredns, kubeadm]
---

> CoreDNS 프로젝트 자체는 "이 버전은 Kubernetes 1.3X를 지원한다"는 별도의
> 공식 Compatibility Matrix를 발행하지 않습니다(표준 client-go watch 기반이라
> apiserver 버전에 느슨하게 결합됨). 대신 kubeadm이 각 Kubernetes minor
> 릴리스마다 기본으로 배포/관리하는 CoreDNS 버전이 정해져 있고, `kubeadm
> upgrade apply` 실행 시 `--skip-phases addon/coredns`로 건너뛰지 않는 한
> 이 기본 버전으로 **자동 업그레이드**됩니다. 아래 표는 그 기본 배포 버전을
> `kubernetes/kubernetes` 소스(`cmd/kubeadm/app/constants/constants.go`,
> `CoreDNSVersion` 상수)에서 각 release 브랜치별로 직접 확인한 값입니다.

## kubeadm 기본 배포 CoreDNS 버전 (실측)

| Kubernetes minor | kubeadm 기본 CoreDNS 버전 |
|---|---|
| 1.32 | v1.11.3 |
| 1.33 | v1.12.0 |
| 1.34 | v1.12.1 |
| 1.35 | v1.13.1 |
| 1.36 | v1.14.2 |

## CoreDNS 1.11.x 계열 (mock 클러스터 현재 버전: v1.11.3)

```yaml
compatibility_matrix:
  component: coredns
  current_version_pattern: "1.11"
  entries:
    - target_kubernetes_minor: "1.32"
      status: COMPATIBLE
      reason: "kubeadm 1.32의 기본 배포 CoreDNS 버전과 정확히 일치합니다(v1.11.3)."
    - target_kubernetes_minor: "1.33"
      status: WARNING
      reason: "kubeadm 1.33의 기본 배포 버전은 v1.12.0입니다. CoreDNS 자체는 API 호환성 문제로 깨지지 않지만, kubeadm upgrade apply 시 자동으로 v1.12.0으로 갱신되므로 현재 v1.11.3을 그대로 유지하려면 --skip-phases addon/coredns가 필요합니다."
      recommendation: "특별한 사유가 없다면 kubeadm의 자동 CoreDNS 업그레이드를 그대로 따르세요(직접 관리 중인 커스텀 CoreDNS 설정이 있다면 Corefile ConfigMap이 덮어써지지 않는지 upgrade 전후로 확인)."
    - target_kubernetes_minor: "1.34"
      status: WARNING
      reason: "kubeadm 1.34의 기본 배포 버전은 v1.12.1입니다. 1.33과 동일한 사유."
      recommendation: "1.33과 동일합니다."
    - target_kubernetes_minor: "1.35"
      status: WARNING
      reason: "kubeadm 1.35의 기본 배포 버전은 v1.13.1로, 현재 버전(v1.11.3)과 두 minor 이상 격차가 벌어집니다."
      recommendation: "kubeadm 자동 업그레이드를 따르거나, 수동 관리 중이라면 CoreDNS를 최소 v1.13 계열로 직접 업그레이드하세요."
    - target_kubernetes_minor: "1.36"
      status: WARNING
      reason: "kubeadm 1.36의 기본 배포 버전은 v1.14.2로, 현재 버전(v1.11.3)과 격차가 가장 큽니다. CoreDNS 자체 하위 호환성 문제로 apiserver 통신이 끊기는 사례는 확인되지 않았으나, 격차가 클수록 CoreDNS 자체의 버그 수정/보안 패치를 놓치게 됩니다."
      recommendation: "1.36 업그레이드 전후로 CoreDNS가 kubeadm 기본 버전(v1.14.2)으로 정상 갱신됐는지 반드시 확인하세요."
```

## 출처

- [kubeadm 소스 — CoreDNSVersion 상수 (release-1.32 ~ release-1.36 브랜치)](https://github.com/kubernetes/kubernetes/blob/release-1.32/cmd/kubeadm/app/constants/constants.go)
- [Upgrading kubeadm clusters — addon 자동 업그레이드 동작](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-upgrade/)
