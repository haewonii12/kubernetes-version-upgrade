---
doc_id: rhel-compatibility-matrix
title: RHEL Compatibility / Requirement
doc_type: os_requirement
component: rhel
applies_to_k8s: ["1.32", "1.33", "1.34", "1.35", "1.36"]
tags: [os, rhel, cgroup]
---

> Kubernetes는 특정 배포판을 공식 인증하지 않으므로, 이 문서는 Kubernetes가
> 명시하는 kernel/cgroup 요구사항(`compatibility-matrix/kernel.md`,
> `compatibility-matrix/cgroup.md`)과 Red Hat 공식 라이프사이클/문서를
> 대조한 결과입니다. 출처는 문서 하단 참고.

## RHEL 8.x 계열

- **라이프사이클**: RHEL 8은 Full Support가 2024-05-31에 종료되었고, 현재
  Maintenance Support 2 단계이며 **2029-05-31**까지 유지됩니다(ELS 애드온 구매
  시 2032~2033까지 연장 가능). RHEL 8.10이 마지막 minor이므로 patch는 이 버전
  안에서만 계속됩니다. **OS 라이프사이클 자체는 2026년 시점에서 급박한 문제가
  아닙니다.**
- **cgroup 기본값**: RHEL 8은 **cgroup v1이 기본값**입니다. cgroup v2는
  `systemd.unified_cgroup_hierarchy=1` 커널 파라미터로 **OS 재설치 없이
  전환 가능**합니다.
- 실제 리스크는 OS 수명이 아니라 cgroup 기본값입니다 — Kubernetes 1.35부터
  kubelet이 cgroup v1 노드에서 기본적으로 기동을 거부합니다
  (`compatibility-matrix/cgroup.md` 참고).

```yaml
compatibility_matrix:
  component: rhel
  current_version_pattern: "8"
  entries:
    - target_kubernetes_minor: "1.32"
      status: WARNING
      reason: "RHEL 8 기본값인 cgroup v1은 이 시점까지는 kubelet 기동에 문제가 없으나, Kubernetes의 cgroup v1 'maintained mode'(1.31부터) 상태입니다."
      recommendation: "장기적으로 cgroup v2 전환(커널 파라미터 변경만으로 가능) 계획을 세우세요."
    - target_kubernetes_minor: "1.33"
      status: WARNING
      reason: "1.32와 동일합니다."
    - target_kubernetes_minor: "1.34"
      status: WARNING
      reason: "1.32와 동일합니다."
    - target_kubernetes_minor: "1.35"
      status: INCOMPATIBLE
      reason: "cgroup v1이 기본값인 RHEL 8 노드에서는, Kubernetes 1.35의 kubelet 기본 설정(FailCgroupV1=true) 때문에 kubelet이 기동을 거부합니다."
      recommendation: "RHEL 8에서 systemd.unified_cgroup_hierarchy=1 커널 파라미터로 cgroup v2로 전환하거나(OS 재설치 불필요), kubelet 설정에서 failCgroupV1: false로 임시 override하세요(장기 지원 경로 아님)."
    - target_kubernetes_minor: "1.36"
      status: INCOMPATIBLE
      reason: "1.35와 동일한 사유입니다."
      recommendation: "1.35와 동일합니다."
```

## RHEL 9.x 계열

- **cgroup 기본값**: RHEL 9는 **cgroup v2가 기본값**입니다.

```yaml
compatibility_matrix:
  component: rhel
  current_version_pattern: "9"
  entries:
    - target_kubernetes_minor: "1.32"
      status: COMPATIBLE
      reason: "cgroup v2가 기본값이라 별도 조치가 필요 없습니다."
    - target_kubernetes_minor: "1.33"
      status: COMPATIBLE
      reason: "cgroup v2가 기본값입니다."
    - target_kubernetes_minor: "1.34"
      status: COMPATIBLE
      reason: "cgroup v2가 기본값입니다."
    - target_kubernetes_minor: "1.35"
      status: COMPATIBLE
      reason: "cgroup v2가 기본값이라 kubelet 기본 거부(FailCgroupV1) 영향을 받지 않습니다."
    - target_kubernetes_minor: "1.36"
      status: COMPATIBLE
      reason: "1.35와 동일합니다."
```

## 출처

- [Red Hat Enterprise Linux 8 라이프사이클 관련 검색 결과](https://tuxcare.com/blog/rhel-8-end-of-life/)
- [Migrating from CGroups V1 to CGroups V2 in RHEL — Red Hat Customer Portal](https://access.redhat.com/articles/3735611)
- [Configuring resource management by using cgroups-v2 and systemd — RHEL 8 공식 문서](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/8/html/managing_monitoring_and_updating_the_kernel/assembly_configuring-resource-management-using-systemd_managing-monitoring-and-updating-the-kernel)
- [About cgroup v2 — Kubernetes 공식 문서](https://kubernetes.io/docs/concepts/architecture/cgroups/)
