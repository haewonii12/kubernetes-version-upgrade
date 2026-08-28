#!/usr/bin/env bash
# 폐쇄망(인터넷 안 되는 환경)에서 실행합니다.
# export-images.sh(docker) 또는 export-images-podman.sh 로 만든 tar 를 이미지로 반입합니다.
#
# 사용법: docker/load-images.sh [tar 파일 (기본: ./k8s-upgrade-images.tar[.gz])]
set -euo pipefail

cd "$(dirname "$0")/.."

ENGINE="$(command -v docker || command -v podman || true)"
[ -n "$ENGINE" ] || { echo "docker 또는 podman 이 필요합니다." >&2; exit 1; }

TAR_FILE="${1:-}"
if [ -z "$TAR_FILE" ]; then
  for f in k8s-upgrade-images.tar.gz k8s-upgrade-images.tar; do
    [ -f "$f" ] && TAR_FILE="$f" && break
  done
fi
if [ -z "$TAR_FILE" ] || [ ! -f "$TAR_FILE" ]; then
  echo "이미지 tar 파일을 찾을 수 없습니다: ${TAR_FILE:-k8s-upgrade-images.tar[.gz]}" >&2
  echo "인터넷 되는 환경에서 docker/export-images.sh 또는 docker/export-images-podman.sh 로 먼저 만들어 반입하세요." >&2
  exit 1
fi

echo "== 이미지 반입 ($TAR_FILE, engine=$(basename "$ENGINE")) =="
case "$TAR_FILE" in
  *.gz) gunzip -c "$TAR_FILE" | "$ENGINE" load ;;
  *)    "$ENGINE" load -i "$TAR_FILE" ;;
esac

# podman 으로 빌드한 이미지는 localhost/ prefix 가 붙는다. docker-compose.yml 은
# prefix 없는 이름을 참조하므로 정규화한다 (docker export 이미지엔 영향 없음).
for img in k8s-upgrade-backend k8s-upgrade-frontend; do
  if "$ENGINE" image inspect "localhost/$img:latest" >/dev/null 2>&1; then
    "$ENGINE" tag "localhost/$img:latest" "$img:latest"
    echo "   retag: localhost/$img:latest -> $img:latest"
  fi
done

echo
echo "완료. 다음으로 기동하세요:"
echo "  docker compose up -d          # 또는  podman compose up -d"
