# 1.32 → 1.36 오프라인 업그레이드 번들

폐쇄망 클러스터를 **Kubernetes 1.32 → 1.36** 으로 순차 업그레이드하는 데 필요한
RPM 패키지 + 컨테이너 이미지 + 검증용 kubeadm 바이너리를 한곳에 모은다.

- **대상 환경**: RHEL 8 / x86_64 / containerd / stacked etcd (kubeadm 클러스터)
- **경로**: 1.32 → 1.33 → 1.34 → 1.35 → 1.36 (minor 건너뛰기 없음, Version Skew Policy)
- **버전 고정**: 모든 patch/이미지 태그는 [`versions.env`](versions.env) 하나에서 관리.
  각 minor 최신 patch 기준(2026-08): 1.33.13 · 1.34.11 · 1.35.8 · 1.36.4
- 정확한 파일/이미지 목록은 [`MANIFEST.md`](MANIFEST.md) (`bash fetch.sh --list` 로 재생성)

```
upgrade-bundle/
├── versions.env         # 단일 버전 소스
├── fetch.sh             # (인터넷 O) 아티팩트 수집 + 전송 tarball 생성
├── push-to-registry.sh  # 이미지 load → 사내 레지스트리용 retag → push
├── load.sh              # (폐쇄망) 각 노드에 RPM 저장소 + 이미지 직접 적재
├── MANIFEST.md          # 수집 대상 전체 목록
└── artifacts/           # fetch.sh 가 채움 (git 미포함)
    ├── rpms/x86_64/*.rpm
    ├── images/k8s-images-v1.3X.tar   # minor별 이미지 묶음
    └── bin/kubeadm-v1.3X.X           # 검증용
```

---

## 1. 인터넷 되는 환경에서 — 수집

```bash
cd upgrade-bundle
bash fetch.sh --resolve     # (선택) 각 minor 최신 patch로 versions.env 갱신
bash fetch.sh               # RPM + 이미지 + 바이너리 수집 → k8s-upgrade-bundle-1.36.tar.gz
```

- 이미지는 `podman`(없으면 `docker`)으로 `--platform linux/amd64` pull 후 minor별 tar로 저장.
- 산출물 `k8s-upgrade-bundle-1.36.tar.gz` (RPM ~200MB + 이미지 ~2.5GB) 하나만 옮기면 된다.

## 2. 폐쇄망으로 반입

승인된 방법(내부망 파일 서버, 반입 매체)으로 `k8s-upgrade-bundle-1.36.tar.gz` 를 옮긴다.

## 3. 이미지 배포 — 두 방식 중 하나

### 3-a. 사내 레지스트리에 push (레지스트리가 있으면 권장)

**한 대(인터넷 X, 레지스트리 접근 O)에서** 이미지를 사내 레지스트리로 올린다:

```bash
tar xzf k8s-upgrade-bundle-1.36.tar.gz && cd upgrade-bundle
podman login registry.corp.local:5000                 # 인증 필요 시
bash push-to-registry.sh registry.corp.local:5000/k8s  # load → retag → push
#   자체서명 레지스트리면:  --tls-verify=false
#   특정 minor만:           --versions "1.33 1.34"
#   매핑만 미리 보기:        --dry-run
```

레이아웃 2가지:
- `--layout kubeadm` (기본): `registry.k8s.io/coredns/coredns:X → <TARGET>/coredns:X` 로 평탄화.
  업그레이드 시 `kubeadm upgrade apply vX --image-repository <TARGET>` 또는
  `kubeadm-config` 의 `ClusterConfiguration.imageRepository: <TARGET>` 로 가리킨다.
- `--layout mirror`: `registry.k8s.io` 경로를 그대로 유지하고, 각 노드 containerd 의
  레지스트리 미러(`/etc/containerd/certs.d/registry.k8s.io/hosts.toml`)로 redirect.
  kubeadm 설정은 건드리지 않는다.

스크립트가 끝나면 사용할 `--image-repository` 값과 태그 매핑
(`artifacts/image-map-<layout>.txt`)을 출력한다.

RPM 은 여전히 각 노드에 배포해야 한다:
```bash
sudo bash load.sh rpms      # file:// dnf 저장소만 등록 (이미지는 레지스트리에서 pull)
```

### 3-b. 각 노드 containerd 에 직접 import (레지스트리 없음)

모든 Control Plane + Worker 노드에서 root로:
```bash
tar xzf k8s-upgrade-bundle-1.36.tar.gz && cd upgrade-bundle
sudo bash load.sh           # RPM 을 file:// dnf 저장소로 등록 + 이미지를 containerd(k8s.io)로 import
```

확인:
```bash
dnf --disablerepo='*' --enablerepo=k8s-upgrade-bundle list available 'kube*'
ctr -n k8s.io images ls | grep -E 'kube-|etcd|coredns|pause'
```

## 4. 업그레이드 실행 (minor 한 단계씩, 1.33 → 1.34 → 1.35 → 1.36)

> 3-a(레지스트리) 방식이면 아래 `kubeadm upgrade apply` 에 `--image-repository <TARGET>` 를
> 추가하거나 `kubeadm-config` 에 `imageRepository` 를 미리 넣어 둔다. 3-b(직접 import)면
> 이미지가 이미 containerd 에 있으므로 그대로 진행한다.

> 전체 절차(Pre-check, drain/uncordon, etcd 백업, 인증서 주의사항)는 이 분석 도구가
> 생성하는 **Upgrade Timeline** 리포트를 따른다. 아래는 아티팩트 사용 요약.

각 minor `X`(예: 1.33.13)에 대해:

**첫 번째 Control Plane 노드**
```bash
dnf install -y kubeadm-1.33.13 --disablerepo='*' --enablerepo=k8s-upgrade-bundle
kubeadm upgrade plan
kubeadm upgrade apply v1.33.13          # 이미지는 이미 containerd에 있으므로 pull 없이 진행
dnf install -y kubelet-1.33.13 kubectl-1.33.13 --disablerepo='*' --enablerepo=k8s-upgrade-bundle
systemctl daemon-reload && systemctl restart kubelet
```

**나머지 Control Plane 노드**
```bash
dnf install -y kubeadm-1.33.13 --disablerepo='*' --enablerepo=k8s-upgrade-bundle
kubeadm upgrade node
dnf install -y kubelet-1.33.13 kubectl-1.33.13 --disablerepo='*' --enablerepo=k8s-upgrade-bundle
systemctl daemon-reload && systemctl restart kubelet
```

**Worker 노드**
```bash
kubectl drain <node> --ignore-daemonsets --delete-emptydir-data
dnf install -y kubeadm-1.33.13 --disablerepo='*' --enablerepo=k8s-upgrade-bundle
kubeadm upgrade node
dnf install -y kubelet-1.33.13 kubectl-1.33.13 --disablerepo='*' --enablerepo=k8s-upgrade-bundle
systemctl daemon-reload && systemctl restart kubelet
kubectl uncordon <node>
```

한 minor가 전부 끝나면(`kubectl get nodes` 모두 새 버전 Ready) 다음 minor로 반복.

---

## 범위에 포함되지 않은 것 (별도 준비)

| 항목 | 이유 |
|---|---|
| RHEL 베이스 의존 패키지(`conntrack-tools`, `socat`, `ethtool`, `iproute-tc` 등) | 이미 kubelet이 돌고 있어 설치돼 있음. 없다면 사내 RHEL 미러에서 조달 |
| **CNI (Calico)** | 이 클러스터는 tigera-operator 1.38.x(Calico 3.30.7). Calico 3.30은 1.35까지 테스트됨 — **1.36 전에 Calico 3.32 계열로 별도 업그레이드 필요**(`rag/documents/compatibility-matrix/calico.md` / `tigera-operator.md` 참고). Calico 이미지/매니페스트는 이 번들에 없음 |
| CoreDNS 커스텀 설정 | kubeadm이 minor별 기본 버전으로 자동 갱신(위 이미지에 포함). 커스텀 Corefile을 쓴다면 덮어쓰기 주의 |
| containerd 자체 업그레이드 | 현재 1.7.x면 1.36까지 동작. 별도 판단(`compatibility-matrix/containerd.md`) |
| etcd 스냅샷 백업 | 업그레이드 전 **반드시** 별도 수행 (`etcdctl snapshot save`) |

## 재현성

- `artifacts/checksums.sha256` 에 모든 파일 SHA-256.
- 나중에 patch가 올라가면 `bash fetch.sh --resolve` 후 다시 `bash fetch.sh`.
