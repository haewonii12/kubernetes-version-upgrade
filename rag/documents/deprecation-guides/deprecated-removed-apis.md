---
doc_id: deprecated-removed-api-guide
title: Kubernetes Deprecated / Removed API Guide
doc_type: removed_api_guide
component: kubernetes
applies_to_k8s: ["1.32", "1.33", "1.34", "1.35", "1.36"]
tags: [deprecated-api, removed-api, flowcontrol, endpoints, volumes, cgroup]
---

> 본 문서는 `rag/documents/release-notes/k8s-1.32.md` ~ `k8s-1.36.md`(공식
> kubernetes.io 블로그/CHANGELOG 근거로 작성됨)에서 확인된 실제 Deprecated/
> Removed API 사실만 반영합니다. 근거가 불확실한 항목은 구조화된 판정 블록에
> 넣지 않고 본문에 UNKNOWN으로 남겨둡니다.

## FlowSchema / PriorityLevelConfiguration v1beta3

`flowcontrol.apiserver.k8s.io/v1beta3`는 **v1.32에서 제거**되었습니다. 대체 API인
`flowcontrol.apiserver.k8s.io/v1`은 v1.29부터 사용 가능했습니다. (기존 샘플
문서의 "1.33 Deprecated / 1.35 제거"는 실제 공식 Deprecation Guide와 다른
잘못된 정보였습니다 — 정확한 "Deprecated in" 버전은 공식 문서에 별도 라벨로
명시되어 있지 않아 아래 entry의 `deprecated_in_version`은 `null`로 둡니다.)

```yaml
deprecated_api_guide:
  entries:
    - kind: FlowSchema
      api_version: flowcontrol.apiserver.k8s.io/v1beta3
      deprecated_in_version: null
      removed_in_version: "1.32"
      replacement_api_version: flowcontrol.apiserver.k8s.io/v1
      notes: >
        v1.32에서 apiserver가 더 이상 이 버전을 서빙하지 않습니다. 대체 API
        flowcontrol.apiserver.k8s.io/v1은 v1.29부터 사용 가능했습니다. v1에서는
        spec.limited.nominalConcurrencyShares를 명시적으로 0으로 지정한 경우
        더 이상 자동으로 30으로 대체되지 않는 동작 차이가 있습니다. 1.32
        이상으로 업그레이드하기 전에 반드시 v1으로 마이그레이션해야 합니다.
    - kind: PriorityLevelConfiguration
      api_version: flowcontrol.apiserver.k8s.io/v1beta3
      deprecated_in_version: null
      removed_in_version: "1.32"
      replacement_api_version: flowcontrol.apiserver.k8s.io/v1
      notes: "FlowSchema와 동일한 일정(v1.32 제거)으로 처리됩니다."
```

## FlowSchema / PriorityLevelConfiguration v1 (현재 GA)

`flowcontrol.apiserver.k8s.io/v1`은 v1.29부터 GA인 안정 버전으로, 이 문서가
다루는 1.32~1.36 구간에서 Deprecated/Removed 이력이 없습니다. 모든 kubeadm
클러스터는 이 API로 된 기본 FlowSchema 13개(`catch-all`, `exempt`, `probes`,
`system-nodes`, `kube-scheduler`, `kube-controller-manager`,
`kube-system-service-accounts`, `service-accounts`, `system-node-high`,
`system-leader-election`, `workload-leader-election`, `endpoint-controller`,
`global-default`)와 기본 PriorityLevelConfiguration을 apiserver가 부트스트랩
시점에 자동 생성합니다 — 사용자가 마이그레이션할 대상이 아닙니다.

```yaml
deprecated_api_guide:
  entries:
    - kind: FlowSchema
      api_version: flowcontrol.apiserver.k8s.io/v1
      deprecated_in_version: null
      removed_in_version: null
      replacement_api_version: null
      notes: "v1.29 GA. 1.32~1.36 구간에서 변경 이력 없음. apiserver가 기본 생성하는 내장 객체."
    - kind: PriorityLevelConfiguration
      api_version: flowcontrol.apiserver.k8s.io/v1
      deprecated_in_version: null
      removed_in_version: null
      replacement_api_version: null
      notes: "v1.29 GA. 1.32~1.36 구간에서 변경 이력 없음. apiserver가 기본 생성하는 내장 객체."
```

## Endpoints v1 (core)

```yaml
deprecated_api_guide:
  entries:
    - kind: Endpoints
      api_version: v1
      deprecated_in_version: "1.33"
      removed_in_version: null
      replacement_api_version: discovery.k8s.io/v1 (EndpointSlice)
      notes: >
        1.33부터 EndpointSlice 사용이 권장되는 방향으로 Deprecated 처리되었으나,
        현재 시점 공식 문서 기준 제거 계획은 없습니다. 계속 서빙되지만 신규
        워크로드는 EndpointSlice로 작성하십시오.
```

## Pod status.resize 필드 (core/v1 Pod)

```yaml
deprecated_api_guide:
  entries:
    - kind: Pod
      api_version: v1
      deprecated_in_version: "1.33"
      removed_in_version: null
      replacement_api_version: null
      notes: >
        Pod.status.resize 필드가 Deprecated 처리되어 더 이상 채워지지 않습니다.
        In-place Pod Resize 진행 상태 확인은 PodResizeInProgress /
        PodResizePending Condition으로 대체되었습니다. (전체 리소스 kind가
        아니라 특정 필드 단위 Deprecation입니다.)
```

## gitRepo Volume (core/v1)

```yaml
deprecated_api_guide:
  entries:
    - kind: Volume(gitRepo)
      api_version: v1
      deprecated_in_version: "1.11"
      removed_in_version: "1.33"
      replacement_api_version: null
      notes: >
        gitRepo volume type이 1.11부터 Deprecated 상태였다가 1.33에서
        제거되었습니다. Init Container + git clone 방식으로 전환하십시오.
        1.36부터는 gitRepo와 별개로 git-repo volume plugin 자체가 기본
        비활성화되어(재활성화 옵션 없음) 이중으로 막혀 있습니다.
```

## Windows Pod hostNetwork: true

```yaml
deprecated_api_guide:
  entries:
    - kind: Pod(Windows hostNetwork)
      api_version: v1
      deprecated_in_version: null
      removed_in_version: "1.33"
      replacement_api_version: null
      notes: "Windows Pod에서 hostNetwork: true 사용이 1.33에서 제거(철회)되었습니다."
```

## Node status.nodeInfo.kubeProxyVersion

```yaml
deprecated_api_guide:
  entries:
    - kind: Node
      api_version: v1
      deprecated_in_version: "1.31"
      removed_in_version: "1.33"
      replacement_api_version: null
      notes: "Node.status.nodeInfo.kubeProxyVersion 필드가 1.31에서 Deprecated, 1.33에서 제거되었습니다."
```

## kubelet cgroupDriver 필드 / --cgroup-driver 플래그

```yaml
deprecated_api_guide:
  entries:
    - kind: KubeletConfiguration(cgroupDriver)
      api_version: kubelet.config.k8s.io
      deprecated_in_version: "1.34"
      removed_in_version: "1.36"
      replacement_api_version: null
      notes: >
        kubelet 설정의 cgroupDriver 필드/--cgroup-driver 플래그가 1.34에서
        Deprecated, 1.36에서 제거되었습니다. CRI(containerd ≥2.0.0, CRI-O
        ≥1.28.0)로부터 cgroup driver를 자동 감지하는 방식(KubeletCgroupDriverFromCRI,
        1.34 GA)으로 전환해야 합니다. 수동 설정을 유지한 채 1.36으로
        업그레이드하면 kubelet이 기동하지 않을 수 있습니다.
```

## Service .spec.trafficDistribution: PreferClose

```yaml
deprecated_api_guide:
  entries:
    - kind: Service(trafficDistribution)
      api_version: v1
      deprecated_in_version: "1.34"
      removed_in_version: null
      replacement_api_version: null
      notes: >
        Service의 trafficDistribution 값 중 PreferClose가 1.34에서 Deprecated
        처리되었고, 1.36부터는 PreferSameZone의 alias로만 동작합니다(값 자체가
        제거되지는 않음). PreferSameZone 또는 PreferSameNode 사용을 권장합니다.
```

## Service .spec.externalIPs

```yaml
deprecated_api_guide:
  entries:
    - kind: Service(externalIPs)
      api_version: v1
      deprecated_in_version: "1.36"
      removed_in_version: "1.43"
      replacement_api_version: null
      notes: >
        보안 우려로 1.36에서 Deprecated 처리되었습니다. 완전 제거는 v1.43
        예정(공식 문서 기준, 시점이 멀어 재확인 권장). LoadBalancer Service,
        NodePort, 또는 Gateway API로의 전환을 권장합니다.
```

## PodDisruptionBudget policy/v1

`policy/v1`은 안정적인 GA API로, 이 문서가 다루는 1.32~1.36 구간에서 Deprecated/
Removed 이력이 없습니다.

```yaml
deprecated_api_guide:
  entries:
    - kind: PodDisruptionBudget
      api_version: policy/v1
      deprecated_in_version: null
      removed_in_version: null
      replacement_api_version: null
      notes: "GA 안정 버전이며 1.32~1.36 구간에서 변경 이력 없음."
```

## HorizontalPodAutoscaler autoscaling/v2

`autoscaling/v2`는 GA 안정 버전이며 이 문서가 다루는 구간에서 변경 이력이 없습니다.

```yaml
deprecated_api_guide:
  entries:
    - kind: HorizontalPodAutoscaler
      api_version: autoscaling/v2
      deprecated_in_version: null
      removed_in_version: null
      replacement_api_version: null
      notes: "GA 안정 버전이며 1.32~1.36 구간에서 변경 이력 없음."
```

## 구조화 판정 대상이 아닌 그 외 Deprecation (참고용, kind/apiVersion 매칭 대상 아님)

아래 항목들은 REST 리소스 kind/apiVersion 단위 Deprecation이 아니라 실행 모드/
클라이언트 설정 단위 변경이라 `lookup_deprecated_api`의 구조화 판정 대상으로
넣지 않았습니다(스키마 오·남용 방지). 필요 시 수동으로 확인하십시오.

- **kube-proxy IPVS 모드**: 1.35에서 Deprecated 처리, nftables 모드로의 전환
  권장 (`k8s-1.35.md` 참고).
- **kubeconfig exec credential plugin `AllowlistEntry.Name` → `AllowlistEntry.Command`
  rename**: 1.36 (`k8s-1.36.md` 참고).
- **`FieldsV1` 직접 필드 접근(client-go)**: 1.36부터 `NewFieldsV1(string)` /
  `GetRawBytes()` 접근자 사용 권장 (`k8s-1.36.md` 참고).

## 출처

- [rag/documents/release-notes/k8s-1.32.md](../release-notes/k8s-1.32.md)
- [rag/documents/release-notes/k8s-1.33.md](../release-notes/k8s-1.33.md)
- [rag/documents/release-notes/k8s-1.34.md](../release-notes/k8s-1.34.md)
- [rag/documents/release-notes/k8s-1.35.md](../release-notes/k8s-1.35.md)
- [rag/documents/release-notes/k8s-1.36.md](../release-notes/k8s-1.36.md)
- [Deprecated API Migration Guide](https://kubernetes.io/docs/reference/using-api/deprecation-guide/)
