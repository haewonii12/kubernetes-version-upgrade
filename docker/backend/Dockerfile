# Build context: repository root (docker-compose.yml 참고)
#
# 폐쇄망 배포 전제: 이 이미지는 인터넷이 되는 환경에서 빌드한 뒤
# `docker save`로 tar로 내보내 폐쇄망으로 반입 → `docker load`로 그대로
# 실행한다 (README "폐쇄망 배포 방법" 참고). 그래서 kubectl-ai 바이너리도
# 빌드 시점에 이 이미지 안에 구워넣어, 반입 후에는 추가 다운로드가 전혀
# 필요 없게 만든다.

# --- kubectl-ai 바이너리 다운로드 (빌드 시점에만 인터넷 필요) ---
FROM debian:bookworm-slim AS kubectl-ai-fetch
# v0.0.29 이하는 --mcp-server 모드에서 내장 kubectl/bash tool이 등록되지
# 않는 버그가 있다 (v0.0.31에서 수정, README 참고) — 반드시 이 버전 이상.
ARG KUBECTL_AI_VERSION=0.0.31
ARG TARGETARCH
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN set -eu; \
    case "$TARGETARCH" in \
      amd64) KUBECTL_AI_ARCH=x86_64 ;; \
      arm64) KUBECTL_AI_ARCH=arm64 ;; \
      *) echo "지원하지 않는 아키텍처: $TARGETARCH" >&2; exit 1 ;; \
    esac; \
    curl -fsSL -o /tmp/kubectl-ai.tar.gz \
      "https://github.com/GoogleCloudPlatform/kubectl-ai/releases/download/v${KUBECTL_AI_VERSION}/kubectl-ai_Linux_${KUBECTL_AI_ARCH}.tar.gz"; \
    tar -xzf /tmp/kubectl-ai.tar.gz -C /tmp kubectl-ai; \
    install -m 0755 /tmp/kubectl-ai /usr/local/bin/kubectl-ai

# --- 실제 런타임 이미지 ---
FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend /app/backend
COPY rag /app/rag
COPY examples /app/examples
COPY --from=kubectl-ai-fetch /usr/local/bin/kubectl-ai /usr/local/bin/kubectl-ai

WORKDIR /app/backend
ENV PYTHONUNBUFFERED=1
# real 모드 분석이 이미지 안에 구워넣은 kubectl-ai를 바로 쓰도록 기본값을 지정한다.
# docker-compose.yml의 environment로 덮어쓸 수 있다.
ENV UPGRADE_AGENT_MCP_SERVER_COMMAND=/usr/local/bin/kubectl-ai
ENV UPGRADE_AGENT_MCP_SERVER_ARGS=--mcp-server

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
