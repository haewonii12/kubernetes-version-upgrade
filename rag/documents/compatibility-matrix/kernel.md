---
doc_id: kernel-requirement
title: Kernel Requirement
doc_type: kernel_requirement
component: kernel
applies_to_k8s: ["1.32", "1.33", "1.34", "1.35", "1.36"]
tags: [kernel]
---

> 공식 Kubernetes Kernel Version Requirements 문서를 근거로 작성된 문서입니다.
> 출처는 문서 하단 참고.

## 4.18.x 계열 (RHEL 8 기본 커널)

**주의**: RHEL의 4.18 커널은 업스트림 4.18과 동일하지 않습니다. Red Hat이 이후
커널의 다수 기능을 4.18 버전 번호를 유지한 채 백포트하기 때문에, 버전 번호만으로
기능 지원 여부를 판단할 수 없습니다. 아래 항목은 "버전 번호 4.18" 기준 공식
요구사항과 대조한 것이며, RHEL 8.10에 실제로 어떤 기능이 백포트되어 있는지는
개별 확인이 필요합니다(공식 문서에서 RHEL 백포트 여부까지는 확인하지 못함 —
Manual Verification 권장).

Kubernetes 공식 문서(Kernel Version Requirements)가 명시하는, 버전과 무관하게
1.32~1.36 전 구간에 걸쳐 있는 기능별 최소 커널 요구사항 중 RHEL 8.10 환경에
관련 있는 항목:

- `net.ipv4.tcp_rmem` / `net.ipv4.tcp_wmem` sysctl (Kubernetes 1.32+): 업스트림
  커널 **4.15+** 필요 — 업스트림 4.18 기준으로는 충족.
- kube-proxy **nftables 모드**: 업스트림 커널 **5.13+** 필요 — 업스트림 4.18
  기준으로는 **미충족**. RHEL 8.10이 이 기능을 백포트했는지는 확인하지 못함.
  IPVS/iptables 모드를 계속 쓴다면 영향 없음.
- Pressure Stall Information(PSI) 메트릭: 업스트림 커널 **4.20+** 및
  `CONFIG_PSI=y` 필요 — 업스트림 4.18 기준으로는 미충족. RHEL 8.10 백포트 여부
  미확인.
- cgroup v2 루트 cgroup의 `cpu.stat` 파일: 업스트림 커널 **5.8+** 필요.
- runc는 freezer 미지원 문제로 **5.2 이상** 커널을 권장(그 미만은 비권장).

```yaml
compatibility_matrix:
  component: kernel
  current_version_pattern: "4.18"
  entries:
    - target_kubernetes_minor: "1.32"
      status: WARNING
      reason: "핵심 kubelet/컨테이너 런타임 동작에는 문제가 없으나, RHEL 백포트 범위를 확인하지 않는 한 버전 번호(4.18)만으로 nftables/PSI 등 고급 기능 지원 여부를 판단할 수 없습니다."
      recommendation: "nftables kube-proxy 모드나 PSI 메트릭을 사용할 계획이 있다면 RHEL 8.10에서 실제 지원 여부를 사전 검증하세요."
    - target_kubernetes_minor: "1.33"
      status: WARNING
      reason: "1.32와 동일한 사유입니다."
    - target_kubernetes_minor: "1.34"
      status: WARNING
      reason: "1.32와 동일한 사유입니다."
    - target_kubernetes_minor: "1.35"
      status: WARNING
      reason: "cgroup v1 자체가 이 버전부터 kubelet 기본 거부 대상이 되므로(compatibility-matrix/cgroup.md 참고), 커널 버전 문제와 별개로 cgroup 설정을 먼저 해결해야 합니다."
      recommendation: "cgroup v2 전환(RHEL 8에서도 커널 파라미터로 가능)을 먼저 검토하세요."
    - target_kubernetes_minor: "1.36"
      status: WARNING
      reason: "1.35와 동일한 사유입니다."
```

## 출처

- [Linux Kernel Version Requirements — Kubernetes 공식 문서](https://kubernetes.io/docs/reference/node/kernel-version-requirements/)
- [Production environment — Kubernetes 공식 문서](https://kubernetes.io/docs/setup/production-environment/)
