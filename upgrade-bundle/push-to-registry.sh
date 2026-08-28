#!/usr/bin/env bash
# 번들의 컨테이너 이미지(artifacts/images/*.tar)를 podman/docker로 load →
# 사내 레지스트리용으로 retag → push 한다.
#
#   bash push-to-registry.sh <TARGET_REPO> [옵션]
#
#   <TARGET_REPO>  목표 레지스트리 + 경로. 예: registry.corp.local:5000/k8s
#
# 레이아웃 2가지:
#   --layout kubeadm   (기본) registry.k8s.io/coredns/coredns:X -> <TARGET>/coredns:X
#                      처럼 마지막 경로만 남긴다. 업그레이드 시:
#                        kubeadm upgrade apply vX.Y.Z --image-repository <TARGET>
#                      (또는 ClusterConfiguration.imageRepository: <TARGET>)
#   --layout mirror    registry.k8s.io 경로를 그대로 유지 -> <TARGET>/coredns/coredns:X.
#                      kubeadm 은 기본값 그대로 두고 containerd 레지스트리 미러
#                      (/etc/containerd/certs.d/registry.k8s.io/hosts.toml) 로 redirect.
#
# 옵션:
#   --engine podman|docker     (기본: 자동)
#   --tls-verify=false         자체서명/사설 CA 레지스트리
#   --authfile <path>          podman 인증 파일 (없으면 미리 `podman login` 필요)
#   --versions "1.33 1.34"     특정 minor 만 (기본: versions.env 의 UPGRADE_PATH)
#   --skip-load                tar load 생략 (이미 엔진에 이미지가 있을 때)
#   --dry-run                  load/tag/push 없이 매핑만 출력
set -euo pipefail
_SELF="$(cd "$(dirname "$0")" && pwd)/$(basename "$0")"
cd "$(dirname "$0")"
source ./versions.env

usage() { sed -n '2,26p' "$_SELF" | sed 's/^# \{0,1\}//'; }
[ $# -ge 1 ] || { usage; exit 1; }
case "$1" in -h|--help) usage; exit 0 ;; esac
TARGET_REPO="${1%/}"; shift

LAYOUT="kubeadm"
ENGINE="${ENGINE:-}"
TLS_ARG=""
AUTH_ARG=""
VERSIONS="$UPGRADE_PATH"
SKIP_LOAD=0
DRY=0
while [ $# -gt 0 ]; do
  case "$1" in
    --layout)        LAYOUT="$2"; shift 2 ;;
    --engine)        ENGINE="$2"; shift 2 ;;
    --tls-verify=false) TLS_ARG="--tls-verify=false"; shift ;;
    --authfile)      AUTH_ARG="--authfile $2"; shift 2 ;;
    --versions)      VERSIONS="$2"; shift 2 ;;
    --skip-load)     SKIP_LOAD=1; shift ;;
    --dry-run)       DRY=1; shift ;;
    *) echo "알 수 없는 옵션: $1" >&2; exit 1 ;;
  esac
done
[ -n "$ENGINE" ] || ENGINE="$(command -v podman || command -v docker || true)"
[ -n "$ENGINE" ] || { echo "podman/docker 가 필요합니다." >&2; exit 1; }
case "$LAYOUT" in kubeadm|mirror) ;; *) echo "--layout 은 kubeadm|mirror" >&2; exit 1 ;; esac

kver() { local u=${1//./_}; eval echo "\$K8S_$u"; }
kv()   { local u=${1//./_} p=$2; eval echo "\$${p}_$u"; }

# fetch.sh 와 동일한 minor별 이미지 목록
image_list() {
  local m=$1 kv; kv=$(kver "$m")
  local c
  for c in kube-apiserver kube-controller-manager kube-scheduler kube-proxy; do
    echo "$REGISTRY/$c:v$kv"
  done
  echo "$REGISTRY/coredns/coredns:$(kv "$m" COREDNS)"
  echo "$REGISTRY/pause:$(kv "$m" PAUSE)"
  echo "$REGISTRY/etcd:$(kv "$m" ETCD)"
}

# registry.k8s.io/<path>:<tag> -> 목표 태그
target_of() {
  local src=$1 tag path
  tag="${src##*:}"
  path="${src%:*}"; path="${path#"$REGISTRY"/}"      # coredns/coredns  또는  kube-apiserver
  if [ "$LAYOUT" = kubeadm ]; then path="${path##*/}"; fi   # kubeadm 레이아웃: 마지막 segment
  echo "$TARGET_REPO/$path:$tag"
}

echo "engine   : $ENGINE"
echo "target   : $TARGET_REPO   (layout=$LAYOUT)"
echo "versions : $VERSIONS"
echo

mkdir -p artifacts
MAP_FILE="artifacts/image-map-$LAYOUT.txt"
: > "$MAP_FILE"
for m in $VERSIONS; do
  tar="artifacts/images/k8s-images-v$m.tar"
  if [ "$SKIP_LOAD" = 0 ] && [ "$DRY" = 0 ]; then
    [ -s "$tar" ] || { echo "!! $tar 없음 — fetch.sh 먼저 실행" >&2; exit 1; }
    echo ">> load $tar"
    "$ENGINE" load -i "$tar" >/dev/null
  fi
  for src in $(image_list "$m"); do
    dst="$(target_of "$src")"
    printf '  %-52s ->  %s\n' "$src" "$dst"
    echo "$src $dst" >> "$MAP_FILE"
    [ "$DRY" = 1 ] && continue
    "$ENGINE" tag "$src" "$dst"
    "$ENGINE" push $TLS_ARG $AUTH_ARG "$dst"
  done
  echo
done

echo "========================================================================"
if [ "$LAYOUT" = kubeadm ]; then
  echo "업그레이드 시 각 minor 마다 --image-repository 로 이 레지스트리를 가리킨다:"
  for m in $VERSIONS; do
    echo "  kubeadm upgrade apply v$(kver "$m") --image-repository $TARGET_REPO   # 첫 CP 노드"
  done
  echo
  echo "또는 kube-system/kubeadm-config 의 ClusterConfiguration 에 고정:"
  echo "  imageRepository: $TARGET_REPO"
else
  echo "kubeadm 은 기본값 그대로. 각 노드 containerd 에 레지스트리 미러 설정:"
  echo "  # /etc/containerd/certs.d/registry.k8s.io/hosts.toml"
  echo "  server = \"https://registry.k8s.io\""
  echo "  [host.\"https://${TARGET_REPO%%/*}\"]"
  echo "    capabilities = [\"pull\", \"resolve\"]"
  echo "  # config_path = \"/etc/containerd/certs.d\" 가 /etc/containerd/config.toml 에 있어야 함 → systemctl restart containerd"
fi
echo
echo "태그 매핑: $MAP_FILE"
