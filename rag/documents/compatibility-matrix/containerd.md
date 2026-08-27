---
doc_id: containerd-compatibility-matrix
title: containerd Compatibility Matrix
doc_type: compatibility_matrix
component: containerd
applies_to_k8s: ["1.32", "1.33", "1.34", "1.35", "1.36"]
tags: [container-runtime, containerd]
---

> 공식 Kubernetes Container Runtime 문서와 containerd 프로젝트 릴리스/지원 정책을
> 근거로 작성된 문서입니다. 출처는 문서 하단 참고.

## containerd 1.6.x 계열

containerd 1.6도 CRI v1을 지원합니다(Kubernetes 공식 문서: "containerd minor version
1.5 and older are not supported in Kubernetes 1.26" — 즉 1.6.0부터 CRI v1 요구사항을
충족). 기능적으로는 1.32~1.36 kubelet과 정상 통신합니다.

다만 containerd 프로젝트 자체의 공식 지원(EOL)이 이미 끝났습니다 — GitHub
`RELEASES.md`의 지원 상태 표 기준 **1.6 브랜치는 2025-08-23에 End of Life** 처리되어
1년 넘게 보안 패치를 받지 못하고 있습니다(1.7 LTS의 EOS는 2026-09-01로 아직 더
남아 있는 것과 대조적입니다).

```yaml
compatibility_matrix:
  component: containerd
  current_version_pattern: "1.6"
  entries:
    - target_kubernetes_minor: "1.32"
      status: WARNING
      reason: "CRI v1을 지원해 kubelet과 기능적으로는 정상 통신하지만, containerd 1.6 브랜치는 2025-08-23에 이미 End of Life 처리되어 1년 넘게 보안 패치를 받지 못하고 있습니다."
      recommendation: "Kubernetes 버전과 무관하게 containerd를 1.7(LTS, EOS 2026-09-01) 이상으로 우선 업그레이드하세요."
    - target_kubernetes_minor: "1.33"
      status: WARNING
      reason: "1.32와 동일한 사유(1.6 브랜치 EOL)입니다."
      recommendation: "1.32와 동일합니다."
    - target_kubernetes_minor: "1.34"
      status: WARNING
      reason: "1.32와 동일한 사유이며, 추가로 cgroup driver 자동 감지(KubeletCgroupDriverFromCRI)도 containerd 2.0+가 필요해 1.6.x에서는 수동 설정을 유지해야 합니다."
      recommendation: "containerd 2.x 업그레이드를 계획하세요."
    - target_kubernetes_minor: "1.35"
      status: WARNING
      reason: "1.6 브랜치 EOL 상태가 1년 넘게 지속되고 있어 리스크가 누적됩니다."
      recommendation: "containerd 2.x 업그레이드 일정을 이 시점 전까지 확정하세요."
    - target_kubernetes_minor: "1.36"
      status: WARNING
      reason: "기능적으로는 여전히 동작하지만(구버전 런타임 fallback 제거는 1.38 예정), 이미 EOL된 런타임을 계속 운영하는 것 자체가 누적 리스크입니다."
      recommendation: "1.36 업그레이드 전 containerd 2.x로의 전환을 강력히 권장합니다."
```

## containerd 1.7.x 계열

containerd 1.7은 CRI v1(Kubernetes가 1.26부터 요구하는 API 버전)을 완전히
지원하므로, 1.32~1.36 전 구간에서 kubelet과의 기본 통신 자체는 문제 없습니다.
다만 두 가지 시한이 다가오고 있습니다.

- **containerd 프로젝트 자체 지원 종료(EOS)**: containerd 1.7 LTS 브랜치의
  End of Support는 **2026-09-01**입니다. 이후에는 보안 패치를 받지 못합니다.
- **kubelet의 CRI RuntimeConfig fallback 제거 예정**: `RuntimeConfig` CRI RPC를
  지원하지 않는 구버전 런타임(containerd 1.x 포함)에 대해 kubelet이
  `--cgroup-driver` 플래그 값으로 fallback하는 동작이 **Kubernetes 1.38에서
  제거될 예정**입니다. 즉, 1.32~1.36 구간 자체에서는 여전히 동작하지만, 이후
  릴리스를 염두에 두면 containerd 2.x 전환을 미리 계획해야 합니다.
- `KubeletCgroupDriverFromCRI`(cgroup driver 자동 감지) 기능은 containerd
  **2.0.0 이상**이 필요합니다. 1.7.x에서는 계속 kubelet/containerd 양쪽에
  cgroup driver를 수동으로 일치시켜야 합니다.

```yaml
compatibility_matrix:
  component: containerd
  current_version_pattern: "1.7"
  entries:
    - target_kubernetes_minor: "1.32"
      status: COMPATIBLE
      reason: "CRI v1을 완전히 지원하며 kubelet 1.32와 정상 통신합니다."
    - target_kubernetes_minor: "1.33"
      status: COMPATIBLE
      reason: "CRI v1을 완전히 지원하며 kubelet 1.33과 정상 통신합니다."
    - target_kubernetes_minor: "1.34"
      status: WARNING
      reason: "동작은 계속되지만 cgroup driver 자동 감지(KubeletCgroupDriverFromCRI)는 containerd 2.0+가 필요해 1.7.x에서는 수동 설정을 유지해야 합니다."
      recommendation: "kubelet과 containerd의 cgroup driver(systemd/cgroupfs)가 일치하는지 수동으로 재확인하세요."
    - target_kubernetes_minor: "1.35"
      status: WARNING
      reason: "containerd 1.7 LTS의 지원 종료(2026-09-01)가 임박했습니다. 기능상으로는 여전히 호환됩니다."
      recommendation: "containerd 2.x 업그레이드 일정을 수립하세요."
    - target_kubernetes_minor: "1.36"
      status: WARNING
      reason: "containerd 1.7 LTS 지원 종료 이후 보안 패치를 받지 못하며, kubelet의 구버전 런타임 fallback 경로도 1.38에서 제거될 예정이라 장기 유지는 불가능합니다."
      recommendation: "1.36 업그레이드 시점을 containerd 2.x 전환과 함께 계획하세요(1.38 이전 완료 목표)."
```

## containerd 2.x 계열

```yaml
compatibility_matrix:
  component: containerd
  current_version_pattern: "2."
  entries:
    - target_kubernetes_minor: "1.32"
      status: COMPATIBLE
      reason: "CRI v1을 완전히 지원합니다."
    - target_kubernetes_minor: "1.33"
      status: COMPATIBLE
      reason: "CRI v1을 완전히 지원합니다."
    - target_kubernetes_minor: "1.34"
      status: COMPATIBLE
      reason: "CRI v1 지원 및 cgroup driver 자동 감지(KubeletCgroupDriverFromCRI)를 활용할 수 있습니다."
    - target_kubernetes_minor: "1.35"
      status: COMPATIBLE
      reason: "CRI v1 지원 및 cgroup driver 자동 감지를 활용할 수 있습니다."
    - target_kubernetes_minor: "1.36"
      status: COMPATIBLE
      reason: "CRI v1 지원 및 cgroup driver 자동 감지를 활용할 수 있으며, 향후(1.38) fallback 제거와도 무관합니다."
```

## 참고 — 다른 문서와의 상충

`release-notes/k8s-1.34.md`, `k8s-1.35.md`는 "1.35가 containerd 1.x를 지원하는
마지막 릴리스이며 1.36부터 지원이 제거된다"고 서술하고 있으나, 이번 조사에서
kubernetes.io 공식 Container Runtimes 문서를 직접 확인한 결과 실제로는 **구버전
런타임 fallback 제거 시점이 1.38**로 명시되어 있어 두 문서 사이에 시점 불일치가
있습니다. 이 문서는 공식 페이지를 직접 인용한 값을 우선 채택했습니다 — 두 문서
중 하나를 대표 근거로 확정하려면 release-notes 쪽도 재확인이 필요합니다.

## 출처

- [Container Runtimes — Kubernetes 공식 문서](https://kubernetes.io/docs/setup/production-environment/container-runtimes/)
- [containerd RELEASES.md (지원 상태 표, 1.6 EOL 2025-08-23 포함)](https://github.com/containerd/containerd/blob/main/RELEASES.md)
- [containerd 1.7 End of Support 관련 검색 결과](https://endoflife.date/containerd)
