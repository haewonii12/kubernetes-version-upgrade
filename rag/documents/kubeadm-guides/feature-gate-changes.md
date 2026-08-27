---
doc_id: feature-gate-changes
title: Feature Gate 변경 이력
doc_type: feature_gate_changes
component: kubernetes
applies_to_k8s: ["1.32", "1.33", "1.34", "1.35", "1.36"]
tags: [feature-gate]
---

> `rag/documents/release-notes/k8s-1.32.md` ~ `k8s-1.36.md`(공식 kubernetes.io
> 블로그/CHANGELOG 근거)에서 확인된 실제 Feature Gate 변경만 정리한 문서입니다.
> 전체 목록이 아니라 클러스터 운영에 영향을 줄 수 있는 항목 위주입니다 — 이
> 목록에 없는 feature gate는 UNKNOWN이며, 해당 minor 버전 release-notes 문서를
> 개별 확인해야 합니다.

## 확인 방법

클러스터에서 사용 중인 custom feature-gate가 있다면(Section 4의 Custom
Configuration 탐지 결과), 목표 버전까지의 경로에서 해당 Feature Gate가
제거되거나 기본값이 변경되지 않았는지 아래 표와 각 minor 버전 Release Note에서
개별적으로 확인해야 한다.

## 버전별 변경 이력

### 1.32

- `DRAControlPlaneController` (Dynamic Resource Allocation, 1.26부터 Alpha) —
  **제거**. DRA 아키텍처가 이 버전에서 크게 재설계되었다.

### 1.33

- Sidecar Containers (`restartPolicy: Always`인 init container) — **Stable
  (GA)** 승격.

### 1.34

- `KubeletCgroupDriverFromCRI` (CRI로부터 cgroup driver 자동 감지) — **GA**.
  containerd ≥2.0.0 또는 CRI-O ≥1.28.0 필요.
- Dynamic Resource Allocation(DRA) 핵심 API — **GA** (`resource.k8s.io/v1`).

### 1.35

- `ControlPlaneKubeletLocalMode`(kubeadm) — **GA**, 기본 활성화.
- In-Place Pod Vertical Resize — **GA**.
- Job `ManagedBy` — **GA**.
- Kubelet Configuration Drop-in Directory — **GA**.
- Image Volume — **GA/기본 활성화**(1.33부터 Beta였음).
- `FailCgroupV1`(kubelet) 기본값이 `false` → **`true`**로 변경 (cgroup v1
  전용 노드에서 kubelet 기동 거부 — `compatibility-matrix/cgroup.md` 참고).

### 1.36

- `DRAResourceClaimGranularStatusAuthorization` — 활성화 시 scheduler/
  controller에 `resourceclaims/binding` update/patch 권한, DRA driver에
  `associated-node:update`/`arbitrary-node:update` 권한을 RBAC으로 별도
  부여해야 한다.

## 출처

- [rag/documents/release-notes/k8s-1.32.md](../release-notes/k8s-1.32.md) ~
  [k8s-1.36.md](../release-notes/k8s-1.36.md)
