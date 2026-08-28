#!/usr/bin/env bash
# 폐쇄망(인터넷 안 되는 환경)에서 실행합니다.
# docker/export-images.sh 로 만든 tar 파일을 이미지로 반입합니다.
#
# 사용법: docker/load-images.sh [tar 파일 경로 (기본값: ./k8s-upgrade-images.tar)]
set -euo pipefail

cd "$(dirname "$0")/.."

TAR_FILE="${1:-k8s-upgrade-images.tar}"
if [ ! -f "$TAR_FILE" ]; then
  echo "이미지 tar 파일을 찾을 수 없습니다: $TAR_FILE" >&2
  echo "인터넷 되는 환경에서 docker/export-images.sh 로 먼저 만들어 반입하세요." >&2
  exit 1
fi

echo "== 이미지 반입 ($TAR_FILE) =="
docker load -i "$TAR_FILE"

echo
echo "완료. 다음으로 기동하세요:"
echo "  docker compose up -d"
