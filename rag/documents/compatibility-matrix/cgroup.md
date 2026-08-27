---
doc_id: cgroup-requirement
title: cgroup v1/v2 Requirement
doc_type: cgroup_requirement
component: cgroup
applies_to_k8s: ["1.32", "1.33", "1.34", "1.35", "1.36"]
tags: [cgroup, kernel]
---

> Kubernetes 공식 cgroup 문서(및 FailCgroupV1 관련 기술된 kubelet 기본 동작
> 변경)를 근거로 작성된 문서입니다. 출처는 문서 하단 참고.

## cgroup v1

- Kubernetes는 **1.31부터 cgroup v1을 "maintained mode"**로 전환했습니다(신규
  기능 추가 없이 유지 보수만 진행).
- **1.35에서 cgroup v1이 공식 Deprecated 상태**(Feature State 문서에 명시)로
  전환되었고, 핵심 변경으로 **kubelet 설정의 `failCgroupV1` 기본값이 `true`로
  바뀌어 cgroup v1 전용 노드에서 kubelet이 기본적으로 기동을 거부**합니다.
- Override 방법은 있습니다(kubelet 설정 파일에서 `failCgroupV1: false`로
  명시) — 하지만 이는 임시방편이며, 공식 Deprecation Policy에 따라 향후
  릴리스에서 완전히 제거될 예정입니다(정확한 제거(Removed) 버전은 공식 문서에
  아직 명시되어 있지 않음 — UNKNOWN, Manual Verification Required).

```yaml
compatibility_matrix:
  component: cgroup
  current_version_pattern: "v1"
  entries:
    - target_kubernetes_minor: "1.32"
      status: WARNING
      reason: "cgroup v1은 1.31부터 'maintained mode'로 전환되어 신규 기능 지원은 중단되었지만, kubelet 기동 자체는 정상입니다."
      recommendation: "cgroup v2 전환 로드맵을 미리 수립하세요."
    - target_kubernetes_minor: "1.33"
      status: WARNING
      reason: "1.32와 동일합니다."
    - target_kubernetes_minor: "1.34"
      status: WARNING
      reason: "1.32와 동일합니다."
    - target_kubernetes_minor: "1.35"
      status: INCOMPATIBLE
      reason: "cgroup v1이 공식 Deprecated 상태로 전환되었고, kubelet의 failCgroupV1 기본값이 true가 되어 cgroup v1 전용 노드에서 kubelet이 기본 설정으로 기동을 거부합니다."
      recommendation: "cgroup v2로 전환하세요. 즉시 전환이 어렵다면 kubelet 설정에서 failCgroupV1: false로 임시 override할 수 있으나, 장기 지원 경로가 아니므로 전환 계획을 병행하세요."
    - target_kubernetes_minor: "1.36"
      status: INCOMPATIBLE
      reason: "1.35와 동일한 사유이며, 완전 제거(Removed) 시점이 아직 공식 문서에 명시되지 않아 override 경로가 언제까지 유효할지도 불확실합니다."
      recommendation: "1.35와 동일합니다."
```

## cgroup v2

```yaml
compatibility_matrix:
  component: cgroup
  current_version_pattern: "v2"
  entries:
    - target_kubernetes_minor: "1.32"
      status: COMPATIBLE
      reason: "cgroup v2는 권장 구성이며 별도 조치가 필요 없습니다."
    - target_kubernetes_minor: "1.33"
      status: COMPATIBLE
      reason: "cgroup v2는 권장 구성입니다."
    - target_kubernetes_minor: "1.34"
      status: COMPATIBLE
      reason: "cgroup v2는 권장 구성입니다."
    - target_kubernetes_minor: "1.35"
      status: COMPATIBLE
      reason: "cgroup v2는 kubelet의 failCgroupV1 기본 동작 영향을 받지 않습니다."
    - target_kubernetes_minor: "1.36"
      status: COMPATIBLE
      reason: "1.35와 동일합니다."
```

## 출처

- [About cgroup v2 — Kubernetes 공식 문서](https://kubernetes.io/docs/concepts/architecture/cgroups/)
- [Linux Kernel Version Requirements — Kubernetes 공식 문서](https://kubernetes.io/docs/reference/node/kernel-version-requirements/)
