#!/usr/bin/env bash
# 인터넷이 되는 환경에서 실행합니다.
# 이미지를 빌드하고, 폐쇄망으로 반입할 tar 파일 하나로 내보냅니다.
#
# 사용법: docker/export-images.sh [출력 디렉터리 (기본값: 저장소 루트)]
set -euo pipefail

cd "$(dirname "$0")/.."

OUT_DIR="${1:-.}"
mkdir -p "$OUT_DIR"
OUT_FILE="$OUT_DIR/k8s-upgrade-images.tar"

echo "== 이미지 빌드 (docker compose build) =="
docker compose build

echo "== 이미지 내보내기 ($OUT_FILE) =="
docker save k8s-upgrade-backend:latest k8s-upgrade-frontend:latest -o "$OUT_FILE"

echo
echo "완료: $OUT_FILE ($(du -h "$OUT_FILE" | cut -f1))"
echo "이 파일과 저장소 전체(특히 docker-compose.yml, rag/documents/)를 폐쇄망으로"
echo "옮긴 뒤, 폐쇄망에서 docker/load-images.sh 를 실행하세요."
