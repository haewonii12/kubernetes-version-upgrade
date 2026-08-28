#!/usr/bin/env bash
# 인터넷이 되는 환경에서 실행. 1.32 → 1.36 순차 업그레이드에 필요한
# RPM + 컨테이너 이미지 + kubeadm 바이너리를 모아 artifacts/ 에 정리하고
# 폐쇄망으로 옮길 단일 tarball(k8s-upgrade-bundle-1.36.tar.gz)을 만든다.
#
#   bash fetch.sh              # 전부 받기
#   bash fetch.sh --resolve    # versions.env 를 각 minor 최신 patch로 갱신만
#   bash fetch.sh --list       # 받을 목록(MANIFEST)만 출력
#
# 필요 도구: curl, tar; 이미지 받기에는 podman 또는 docker.
set -euo pipefail
cd "$(dirname "$0")"
source ./versions.env

ART="artifacts"
RPMDIR="$ART/rpms/$RPM_ARCH"
IMGDIR="$ART/images"
BINDIR="$ART/bin"
ENGINE="${ENGINE:-$(command -v podman || command -v docker || true)}"

minors() { echo $UPGRADE_PATH; }
kver()   { local u=${1//./_}; eval echo "\$K8S_$u"; }
kv()     { local u=${1//./_} p=$2; eval echo "\$${p}_$u"; }

rpm_repo() { printf "$RPM_REPO_BASE" "$1"; }

# minor 하나에 필요한 RPM 파일명 (RHEL/x86_64, 최신 patch 기준)
rpm_files() {
  local m=$1 kv; kv=$(kver "$m")
  echo "kubeadm-${kv}-150500.1.1.${RPM_ARCH}.rpm"
  echo "kubelet-${kv}-150500.1.1.${RPM_ARCH}.rpm"
  echo "kubectl-${kv}-150500.1.1.${RPM_ARCH}.rpm"
  echo "cri-tools-$(kv "$m" CRITOOLS)-150500.1.1.${RPM_ARCH}.rpm"
  echo "kubernetes-cni-$(kv "$m" CNI)-150500.1.1.${RPM_ARCH}.rpm"
}

# minor 하나에 필요한 컨테이너 이미지 (kubeadm config images list)
image_list() {
  local m=$1 kv; kv=$(kver "$m")
  for c in kube-apiserver kube-controller-manager kube-scheduler kube-proxy; do
    echo "$REGISTRY/$c:v$kv"
  done
  echo "$REGISTRY/coredns/coredns:$(kv "$m" COREDNS)"
  echo "$REGISTRY/pause:$(kv "$m" PAUSE)"
  echo "$REGISTRY/etcd:$(kv "$m" ETCD)"
}

do_resolve() {
  echo ">> 각 minor 최신 patch 확인 중..."
  for m in $(minors); do
    v=$(curl -fsSL "https://dl.k8s.io/release/stable-$m.txt"); v=${v#v}
    sed -i "s/^K8S_${m//./_}=.*/K8S_${m//./_}=\"$v\"/" versions.env
    echo "   $m -> $v"
  done
  echo ">> versions.env 갱신 완료. 이미지 태그(coredns/pause/etcd)는 직접 확인 필요:"
  for m in $(minors); do echo "   kubeadm-$m: kubeadm config images list --kubernetes-version=v$(kver "$m")"; done
}

do_list() {
  echo "# 업그레이드 번들 대상 목록  (경로: 1.32 -> ${UPGRADE_PATH// / -> })"
  for m in $(minors); do
    echo; echo "## v$m  (patch $(kver "$m"))"
    echo "### RPM ($RPM_ARCH)"; rpm_files "$m" | sed 's/^/  - /'
    echo "### 컨테이너 이미지 ($IMAGE_PLATFORM)"; image_list "$m" | sed 's/^/  - /'
  done
}

do_fetch() {
  mkdir -p "$RPMDIR" "$IMGDIR" "$BINDIR"

  echo ">> RPM 다운로드"
  for m in $(minors); do
    base="$(rpm_repo "$m")/$RPM_ARCH"
    for f in $(rpm_files "$m"); do
      [ -s "$RPMDIR/$f" ] && { echo "   = $f"; continue; }
      echo "   + $f"
      curl -fsSL -o "$RPMDIR/$f" "$base/$f"
    done
  done

  echo ">> kubeadm 바이너리 (검증용, linux/amd64)"
  for m in $(minors); do
    v=$(kver "$m")
    [ -s "$BINDIR/kubeadm-v$v" ] || curl -fsSL -o "$BINDIR/kubeadm-v$v" \
      "https://dl.k8s.io/release/v$v/bin/linux/amd64/kubeadm"
    chmod +x "$BINDIR/kubeadm-v$v"
  done

  [ -n "$ENGINE" ] || { echo "!! podman/docker 없음 — 이미지 단계 건너뜀"; return; }
  echo ">> 컨테이너 이미지 pull + save  (engine: $ENGINE)"
  for m in $(minors); do
    tar="$IMGDIR/k8s-images-v$m.tar"
    [ -s "$tar" ] && { echo "   = $tar"; continue; }
    imgs=$(image_list "$m")
    for i in $imgs; do
      echo "   pull $i"
      "$ENGINE" pull --platform "$IMAGE_PLATFORM" "$i" >/dev/null
    done
    echo "   save -> $tar"
    # podman은 다중 이미지를 하나의 docker-archive로 넣을 때 -m 필요(없으면 첫 이미지만 저장하고
    # 나머지 태그를 거기에 붙이는 손상된 아카이브가 나온다). docker save는 -m 없이도 정상.
    case "$ENGINE" in
      *podman) "$ENGINE" save -m -o "$tar" $imgs ;;
      *)       "$ENGINE" save -o "$tar" $imgs ;;
    esac
  done
}

do_package() {
  echo ">> 체크섬"
  ( cd "$ART" && find . -type f ! -name checksums.sha256 -exec sha256sum {} + | sort -k2 > checksums.sha256 )
  do_list > MANIFEST.md
  local out="k8s-upgrade-bundle-1.36.tar.gz"
  echo ">> $out 생성"
  tar czf "$out" versions.env fetch.sh push-to-registry.sh load.sh README.md MANIFEST.md "$ART"
  echo
  echo "완료: $(du -h "$out" | cut -f1)  $out"
  echo "폐쇄망으로 옮긴 뒤 각 노드에서:  tar xzf $out && sudo bash load.sh"
}

case "${1:-all}" in
  --resolve) do_resolve ;;
  --list)    do_list ;;
  all|"")    do_fetch && do_package ;;
  *) echo "usage: $0 [--resolve|--list]"; exit 1 ;;
esac
