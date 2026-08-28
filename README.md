# Kubernetes Upgrade Assistant

현재 Kubernetes 클러스터 상태(버전, HA 구성, etcd, OS/Kernel/cgroup, Container
Runtime, CNI/CSI, 설치된 소프트웨어, Custom Configuration, 사용 중인 API 등)를
Read-Only로 수집하고, RAG로 관리되는 Release Note / Compatibility 문서를
근거로 해당 클러스터 전용 Kubernetes Upgrade Plan을 생성하는 Agent입니다.

> **모든 판단은 근거 기반입니다.** RAG 문서에 근거가 없는 Compatibility/Deprecated
> API 판단은 절대 추측하지 않고 `UNKNOWN` (Manual Verification Required)으로
> 표시합니다.

## Architecture

```text
                    ┌────────────────────┐
                    │ RAG (rag/documents) │   ← 문서만 추가하면 코드 수정 없이 반영
                    └─────────┬──────────┘
                              │
                    ┌─────────▼──────────┐
React UI ──────────►│ FastAPI Backend    │
  (SSE 진행 표시)    │  LangGraph Agent   │
                    │  Collector / Risk  │
                    └─────────┬──────────┘
                              │ MCP (stdio)
                    ┌─────────▼──────────┐
                    │ kubectl-ai MCP     │  ← Read-Only (get/list/watch)
                    │ Server             │
                    └─────────┬──────────┘
                              │
                    ┌─────────▼──────────┐
                    │ Kubernetes Cluster │
                    └────────────────────┘
```

상세 설계는 [`docs/architecture.md`](docs/architecture.md) 참고. LangGraph 노드
흐름은 `collect_cluster → analyze_cluster → detect_custom_config →
detect_installed_software → search_rag → check_compatibility →
check_deprecated_api → analyze_risk → generate_upgrade_path →
generate_upgrade_plan` 순서입니다 (`backend/app/agents/upgrade_agent.py`).

## Directory Structure

```text
backend/    FastAPI + LangGraph Agent + Collector + RAG Retriever
frontend/   React + TypeScript + Tailwind SPA
rag/        RAG 문서 원본(documents/) 및 색인 미리보기 스크립트(ingestion/)
docker/     Backend/Frontend Dockerfile, kubectl-ai RBAC 예시
docs/       설계 문서
examples/   Mock Cluster Fixture (실제 클러스터 없이 데모 가능)
```

## Requirements

- Python 3.12+, Node.js 20+ (Local 실행 시)
- Docker / Docker Compose (Compose 실행 시)
- 실제 클러스터 분석 시: Read-Only RBAC이 적용된 kubeconfig (`docker/mcp/rbac.yaml` 참고). Local 실행이라면
  [kubectl-ai](https://github.com/GoogleCloudPlatform/kubectl-ai) MCP 서버 바이너리도 직접 준비해야 하지만,
  Docker Compose로 실행하면 백엔드 이미지 안에 이미 구워져 있어 별도 준비가 필요 없습니다.

## 실행 방법 — Docker Compose (권장)

```bash
docker compose up -d --build
```

브라우저에서 `http://localhost:3000` 접속. 백엔드 API는 `http://localhost:8000`.

## 실행 방법 — Kubernetes

`deploy/k8s/` 에 Deployment + Service + Ingress 매니페스트가 있다.

```bash
# deploy/k8s/ingress.yaml 의 host 를 실제 도메인으로 수정한 뒤
kubectl apply -k deploy/k8s/
```

자세한 내용(이미지 배포 방식, backend replicas=1 이유, SSE 버퍼링, RAG 문서 갱신 등)은
[`deploy/k8s/README.md`](deploy/k8s/README.md) 참고.

## 폐쇄망 배포 방법

인터넷이 되는 환경에서 이미지를 빌드해 tar로 내보낸 뒤, 폐쇄망으로 반입해서 그대로 실행합니다.
kubectl-ai 와 pluto(Deprecated API 교차검증) 바이너리도 빌드 시점에 백엔드 이미지 안에
구워지므로(pluto는 데이터셋을 바이너리에 내장), 반입 후에는 추가 다운로드가 전혀 필요
없습니다 — 컨테이너만 뜨면 real 모드 분석까지 바로 됩니다.

**1. 인터넷이 되는 환경에서:**

```bash
git clone <repo> && cd k8s-upgrade-assistant
docker/export-images.sh          # docker: compose build + save → k8s-upgrade-images.tar
# 또는 podman:
docker/export-images-podman.sh   # podman build(--platform linux/amd64) + save → k8s-upgrade-images.tar.gz
#   빌드 머신이 arm64면 qemu 에뮬레이션으로 amd64 cross-build (qemu-user-static/binfmt 필요)
#   대상이 arm64면:  docker/export-images-podman.sh --arch arm64
```

**2. 저장소 전체(특히 `k8s-upgrade-images.tar[.gz]`, `docker-compose.yml`, `rag/documents/`)를 폐쇄망으로 반입**

승인된 방법(내부망 파일 서버, 반입 매체 등)으로 옮깁니다.

**3. 폐쇄망 안에서:**

```bash
docker/load-images.sh     # docker/podman 자동 감지, .tar/.tar.gz 자동 처리
docker compose up -d      # 또는 podman compose up -d  (이미지가 이미 있으므로 --build 불필요)
```

이후 RAG 문서(`rag/documents/`)를 갱신할 때도 같은 방식입니다 — 문서만 폐쇄망 안에서 직접
고치고 `docker compose restart backend`만 하면 되며(볼륨 마운트라 이미지 재반입 불필요),
코드 자체가 바뀌었을 때만 1~3 과정을 다시 반복하면 됩니다.

## 실행 방법 — Local

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev   # http://localhost:3000, /api 요청은 8000으로 proxy
```

## Mock Mode 실행 방법

실제 클러스터 없이 전체 파이프라인(수집 → Custom Config 탐지 → Software
Inventory → RAG 검색 → Compatibility/Deprecated API 검사 → Risk 분석 →
Upgrade Plan 생성)을 검증할 수 있습니다.

Web UI에서 "Mock 모드 사용" 체크박스를 켜고 Target Version을 선택한 뒤
"클러스터 분석"을 누르면 됩니다. Mock 데이터는 `examples/mock-cluster/*.json`
(kubectl get -o json 형식)에 있으며, 다음 시나리오를 담고 있습니다.

- Kubernetes 1.32.13, Control Plane 3대(HA, stacked etcd), Worker 1대
- RHEL 8.10 / Kernel 4.18.x / cgroup v1(추정) / containerd 1.7.30
- Calico 3.30.7, cert-manager 1.17.1, ingress-nginx 1.12.0, ArgoCD 2.13.2,
  Prometheus/Prometheus Operator, CoreDNS, kube-proxy 등
- kube-apiserver Custom Configuration: `--encryption-provider-config`,
  `--audit-policy-file`, `--audit-log-path`
- `flowcontrol.apiserver.k8s.io/v1beta3` 사용 중인 FlowSchema (1.35에서 제거 예정 → Deprecated API 검사 데모)

API로 직접 호출하려면:

```bash
curl -X POST http://localhost:8000/api/v1/analysis \
  -F target_kubernetes_version=1.36 -F mock_mode=true
# => {"analysis_id": "..."}
curl http://localhost:8000/api/v1/analysis/<id>/events   # SSE 진행 상황
curl http://localhost:8000/api/v1/analysis/<id>/report   # 완료 후 결과
```

## kubectl-ai MCP 연결 방법 (실제 클러스터)

1. `docker/mcp/rbac.yaml`을 대상 클러스터에 적용해 get/list/watch 전용
   ServiceAccount를 만듭니다.
2. 해당 ServiceAccount 기준 kubeconfig를 발급받습니다.
3. Web UI에서 "Mock 모드 사용" 체크를 해제하고 kubeconfig 파일을 업로드합니다.
4. Backend는 업로드된 kubeconfig를 임시 파일로 저장한 뒤 `kubectl-ai`를 MCP
   stdio 서버로 기동해 연결하고, 분석 종료 즉시 해당 임시 파일을 삭제합니다
   (`backend/app/services/analysis_service.py`).

`backend/app/mcp/client.py`의 `RealMCPClient`는 실제 kubectl-ai 프로세스(로컬
k3s 클러스터 대상)로 End-to-End 검증을 완료했습니다 — 세션 연결/각 tool 호출에
timeout이 걸려 있어, kubectl-ai가 응답하지 않아도 무한 대기 대신 수십 초 내에
명확한 에러로 끝납니다.

**중요 — kubectl-ai 버전 요구사항**: kubectl-ai **v0.0.29 이하**에는
`--mcp-server` 모드에서 내장 `kubectl`/`bash` tool이 아예 등록되지 않는 버그가
있습니다 (v0.0.31에서 ["fix: register built-in tools (bash, kubectl) in MCP
server mode"](https://github.com/GoogleCloudPlatform/kubectl-ai/pull/643)로
수정됨). 이 버그가 있는 버전을 쓰면 Real 모드 분석이 "tool 'kubectl' not
found" 에러로 즉시 실패합니다(더 이상 무한정 멈추지는 않습니다). **kubectl-ai
v0.0.31 이상**을 사용하세요:

```bash
kubectl-ai version   # 0.0.31 미만이면 아래에서 최신 버전을 받아 교체
```

시스템 전역 바이너리를 바꿀 권한이 없다면, 사용자 홈 등 별도 경로에 최신
바이너리를 받아 `UPGRADE_AGENT_MCP_SERVER_COMMAND` 환경변수로 그 경로를
가리키면 됩니다 (`.env.example` 참고).

## RAG 문서 추가 방법

`rag/documents/**/*.md`에 frontmatter + `## 섹션` + (필요 시) 구조화된
` ```yaml compatibility_matrix ``` ` / ` ```yaml deprecated_api_guide ``` `
블록을 추가하면 **코드 수정 없이** 다음 백엔드 기동 시 자동으로 검색/판정에
반영됩니다. 자세한 형식은 [`rag/documents/README.md`](rag/documents/README.md)
참고. 문법 검증만 하고 싶다면:

```bash
cd rag/ingestion && python3 build_index.py
```

> 저장소에 포함된 RAG 문서는 **PoC용 샘플 데이터**입니다. 운영 적용 전 각
> 컴포넌트의 공식 Release Note / Compatibility Matrix로 교체하세요.

## LLM 연동 (선택사항) — RAG 검색 결과를 "생성"으로 확장

기본 상태에서는 RAG가 **검색(Retrieval)까지만** 합니다 — Compatibility/Risk/
Deprecated API 판정은 항상 `rag/documents/*.md`의 구조화된 룰 기반이며, 이
판정 로직에는 LLM이 전혀 관여하지 않습니다 (No Hallucination 원칙, Section 25).

Web UI의 "LLM 설정" 항목에 **OpenAI 호환 `/v1/chat/completions` API**를 쓰는
서버(로컬 Ollama, vLLM, LM Studio 등)의 Endpoint와 Model을 입력하면, 검색된
근거를 바탕으로 다음 두 곳에 자연어 요약이 추가로 "생성"됩니다 (`backend/app/llm/client.py`).

- 각 Version Phase의 Release Note 요약 (`agents/planner.py`)
- 리포트 최상단 전체 요약 (`services/analysis_service.py`)

두 값을 비워두면 이전과 동일하게 RAG 검색 결과 원문 발췌만 표시됩니다.
LLM 호출이 실패/타임아웃(30초)돼도 분석 전체가 실패하지 않고 조용히 원문
발췌로 fallback합니다 — LLM은 어디까지나 "있으면 좋은" 부가 기능입니다.
생성된 텍스트는 프론트엔드에서 "AI 생성" 배지로 항상 구분 표시됩니다.

## 보안 주의사항

- kubeconfig는 분석 세션 동안만 임시 파일로 저장되고, 분석 완료/실패 직후
  즉시 삭제됩니다 (`analysis_service.run_analysis`의 `finally` 블록).
- 로그에는 `token`, `client-key-data`, `client-certificate-data`, `password`
  등 민감 필드가 패턴 매칭으로 자동 마스킹됩니다 (`app/core/logging.py`).
- MCP 연동은 기본적으로 get/list/watch만 허용합니다. create/update/patch/
  delete는 코드 상에서 제공하지 않으며, 클러스터 RBAC(`docker/mcp/rbac.yaml`)
  으로도 동일하게 제한할 것을 권장합니다.
- Upgrade 실행 명령은 항상 "제안"으로만 표시되며 Agent가 직접 실행하지
  않습니다.

## 향후 확장 방법

- **Upgrade 실행 자동화 / Dry Run**: `app/agents/planner.py`가 생성하는
  `UpgradeCommand`를 실제 실행 계층(승인 절차 포함)에 연결.
- **Node Drain/순차 Upgrade 자동화**: MCP RBAC을 단계적으로 완화하고,
  사용자 승인(2단계 확인) 후에만 실행하는 별도 "Execution Agent" 추가.
- **Multi Cluster / Upgrade History**: `app/services/analysis_service.py`의
  Snapshot 저장 방식을 DB로 교체하고 클러스터 식별자를 키에 추가.
- **RAG 고도화**: 현재 TF-IDF 기반 `RAGRetriever`(`app/rag/retriever.py`)를
  동일 인터페이스(`search`, `lookup_compatibility`, `lookup_deprecated_api`)를
  유지한 채 OpenSearch/Vector DB 구현체로 교체.
- **Air-gapped 패키지 저장소 연동**: `docs/architecture.md`의 폐쇄망 원칙에
  따라, Upgrade Command 생성 시 사내 dnf/apt 미러 주소를 설정으로 주입.
