#!/usr/bin/env bash
# export-images.sh 의 podman 판. 인터넷이 되는 환경에서 실행한다.
# backend/frontend 이미지를 빌드해 폐쇄망 반입용 tar 하나로 내보낸다.
#
# 사용법: docker/export-images-podman.sh [출력 디렉터리 (기본: 저장소 루트)] [--arch amd64|arm64]
#
# 기본 대상은 linux/amd64 (폐쇄망 분석기 호스트가 x86_64). 빌드 머신이 arm64면
# qemu 에뮬레이션으로 cross-build 하며, qemu binfmt 가 등록돼 있어야 한다.
set -euo pipefail
cd "$(dirname "$0")/.."

OUT_DIR="."
PLATFORM="linux/amd64"
while [ $# -gt 0 ]; do
  case "$1" in
    --arch)     PLATFORM="linux/$2"; shift 2 ;;
    -h|--help)  sed -n '2,7p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *)          OUT_DIR="$1"; shift ;;
  esac
done
mkdir -p "$OUT_DIR"
OUT="$OUT_DIR/k8s-upgrade-images.tar"
BACKEND=k8s-upgrade-backend:latest
FRONTEND=k8s-upgrade-frontend:latest

command -v podman >/dev/null || { echo "podman 이 필요합니다." >&2; exit 1; }
HOST_ARCH="$(podman info -f '{{.Host.Arch}}' 2>/dev/null || echo unknown)"

# --- cross-build 이면 qemu binfmt 확인 ---
if [ "linux/$HOST_ARCH" != "$PLATFORM" ]; then
  qarch="${PLATFORM##*/}"; [ "$qarch" = amd64 ] && qarch=x86_64
  if [ ! -e "/proc/sys/fs/binfmt_misc/qemu-$qarch" ]; then
    echo "!! $PLATFORM 에뮬레이션(qemu-$qarch)이 등록돼 있지 않습니다." >&2
    echo "   등록:  podman run --rm --privileged docker.io/tonistiigi/binfmt --install $qarch" >&2
    echo "   또는 $PLATFORM 네이티브 머신에서 실행하세요." >&2
    exit 1
  fi
  echo "== cross-build: $HOST_ARCH 호스트에서 $PLATFORM 빌드 (qemu-$qarch) =="
fi

# --- 공개 base 이미지는 익명으로 받는다 (호스트에 만료/오류 레지스트리 토큰이 있어도 무방) ---
ANON="$(mktemp)"; printf '{"auths":{}}' > "$ANON"
FE_CTX=""
cleanup() { rm -f "$ANON"; [ -n "$FE_CTX" ] && rm -rf "$FE_CTX"; }
trap cleanup EXIT

echo "== base 이미지 pull ($PLATFORM) =="
for b in debian:bookworm-slim python:3.12-slim nginx:1.27-alpine; do
  echo "   $b"
  podman pull -q --platform "$PLATFORM" --authfile "$ANON" "docker.io/library/$b" >/dev/null
done

# --- backend: 컨테이너 안에서 빌드 (pip 는 emulated 여도 wheel 이라 안전) ---
echo "== backend 이미지 빌드 =="
podman build --platform "$PLATFORM" --authfile "$ANON" -t "$BACKEND" -f docker/backend/Dockerfile .

# --- frontend: 정적 산출물(dist/)은 아키텍처 무관 → 호스트에서 네이티브 빌드 후 nginx 에 얹는다.
#     (emulated node 로 npm 을 돌리면 qemu 가 SIGSEGV 나는 경우가 잦음) ---
command -v npm >/dev/null || { echo "frontend 빌드에 npm(node)이 필요합니다." >&2; exit 1; }
echo "== frontend 정적 빌드 (호스트 네이티브) =="
( cd frontend && npm ci --no-audit --no-fund --silent && npm run build )

echo "== frontend 이미지 빌드 ($PLATFORM, RUN 없음) =="
FE_CTX="$(mktemp -d)"
cp -r frontend/dist "$FE_CTX/dist"
cp docker/frontend/nginx.conf "$FE_CTX/nginx.conf"
cp docker/frontend/Dockerfile.prebuilt "$FE_CTX/Containerfile"
podman build --platform "$PLATFORM" --authfile "$ANON" -t "$FRONTEND" "$FE_CTX"

echo "== 이미지 내보내기 ($OUT.gz) =="
# -m: 두 이미지를 개별 항목으로 저장 (없으면 하나로 뭉개지는 podman 버그)
podman save --format docker-archive -m -o "$OUT" "$BACKEND" "$FRONTEND"
gzip -f "$OUT"

echo
echo "완료: $OUT.gz  ($(du -h "$OUT.gz" | cut -f1))"
echo
echo "이 파일 + 저장소 전체(docker-compose.yml, rag/documents/)를 폐쇄망으로 옮긴 뒤:"
echo "  bash docker/load-images.sh $(basename "$OUT").gz"
echo "  docker compose up -d          # 또는  podman compose up -d"
