# Kubernetes Upgrade Agent — Architecture (Step 1)

> 이 문서는 구현 이전 단계의 설계 문서입니다. Step 2(Domain Model) 이후부터 실제 코드가
> 이 구조를 채워나갑니다. 코드가 구조와 어긋나면 이 문서를 먼저 갱신합니다.

## 0. 설계 원칙 (모든 구현이 지켜야 하는 제약)

| 원칙 | 의미 |
|---|---|
| Read Only First | PoC 단계에서 Cluster에 대한 쓰기 동작(create/update/patch/delete)은 MCP RBAC 및 코드 양쪽에서 차단 |
| Evidence Based | Compatibility/Risk 판단은 반드시 RAG 검색 결과(document, section)를 근거로 첨부 |
| No Hallucination | RAG에 근거가 없으면 `UNKNOWN` / `Manual Verification Required`로 명시, 추측 금지 |
| DRY | 동일한 kubectl 조회를 여러 Node/모듈에서 중복 호출하지 않도록 Collector 계층에서 캐싱·재사용 |
| Modular / 책임 분리 | Collector(수집) ↔ Analyzer(판단) ↔ RAG(근거) ↔ Agent(orchestration) ↔ API/UI 는 서로의 내부 구현을 몰라도 되게 인터페이스로만 통신 |
| Compatibility Rule 비하드코딩 | "Calico 3.30은 K8s 1.36과 호환" 같은 규칙은 코드가 아니라 RAG 문서(`rag/documents/`)에 존재. 코드는 오직 "검색 → 근거 있으면 판정, 없으면 UNKNOWN"만 수행 |
| 폐쇄망 대응 | Runtime에 외부 인터넷 호출 없음. Release Note/Compatibility 자료는 사전에 RAG에 적재된 정적 문서만 사용. Docker 이미지 자체도 kubectl-ai 바이너리까지 빌드 시점에 구워넣어, 인터넷 되는 곳에서 빌드 → `docker save`/`docker load`로 반입하면 폐쇄망 안에서 추가 다운로드 없이 그대로 기동 가능 (`docker/export-images.sh`/`docker/load-images.sh`, README "폐쇄망 배포 방법" 참고) |

---

## 1. 전체 아키텍처

```text
                         ┌───────────────────────────────┐
                         │   RAG (Vector DB + Documents)  │
                         │   - Release Notes              │
                         │   - Deprecated/Removed API      │
                         │   - Version Skew Policy         │
                         │   - Compatibility Matrix        │
                         │     (Calico/Cilium/containerd/  │
                         │      CRI-O/CSI/Ingress/         │
                         │      cert-manager/Prometheus/    │
                         │      ArgoCD/RHEL/Kernel/cgroup)  │
                         └───────────────┬─────────────────┘
                                         │ retriever
                                         ▼
┌──────────┐   REST/SSE    ┌───────────────────────────────┐
│ Frontend │◄─────────────►│        FastAPI Backend         │
│ (React)  │               │  ┌───────────────────────────┐ │
└──────────┘               │  │   LangGraph Upgrade Agent  │ │
                            │  │                            │ │
                            │  │ collect → analyze →        │ │
                            │  │ custom_config →             │ │
                            │  │ software_inventory →        │ │
                            │  │ rag_search →                │ │
                            │  │ compatibility →              │ │
                            │  │ deprecated_api →              │ │
                            │  │ risk → upgrade_path →         │ │
                            │  │ upgrade_plan                  │ │
                            │  └──────────────┬────────────┘ │
                            └─────────────────┼──────────────┘
                                              │ MCP (stdio/http)
                                              ▼
                            ┌───────────────────────────────┐
                            │   kubectl-ai MCP Server         │
                            │   (Read-Only RBAC: get/list/    │
                            │    watch 만 허용)                │
                            └───────────────┬───────────────┘
                                            │ kubectl / bash
                                            ▼
                            ┌───────────────────────────────┐
                            │      Kubernetes Cluster         │
                            └───────────────────────────────┘
```

Mock 모드에서는 MCP Client가 실제 kubectl-ai 대신 `examples/mock-cluster/`의
고정 응답을 반환하는 동일 인터페이스 구현체로 교체됩니다 (Strategy 패턴).

---

## 2. LangGraph 노드 흐름과 책임 분리

```text
START
  │
  ▼
collect_cluster            → Collector 계층 호출, ClusterInfo 원시 데이터 조립
  │
  ▼
analyze_cluster            → Node/OS/Kernel/cgroup/HA/etcd topology 판단
  │
  ▼
detect_custom_config       → 4대 manifest에서 kubeadm 기본값 diff → CustomConfig[]
  │
  ▼
detect_installed_software  → 전 Namespace 리소스 + 이미지 태그 → SoftwareInventory[]
  │
  ▼
search_rag                 → 위 결과를 쿼리로 RAG 검색 (버전별 Release Note,
                              Compatibility Matrix, Deprecated API Guide)
  │
  ▼
check_compatibility        → RAG 근거 매핑 → CompatibilityResult[] (COMPATIBLE/
                              INCOMPATIBLE/UNKNOWN, source 포함)
  │
  ▼
check_deprecated_api       → 실 클러스터 API 사용 현황 × 목표 버전까지의 제거/폐기 목록
  │
  ▼
analyze_risk                → 위 모든 결과 종합 → RiskFinding[] (BLOCKER~INFO) + Readiness Score
  │
  ▼
generate_upgrade_path       → minor version 순차 경로 계산 (skip 금지)
  │
  ▼
generate_upgrade_plan       → 경로의 각 단계에 Pre-check/CP순차업그레이드/Worker/Post-check +
                               실행 명령 제안 바인딩 → UpgradePlan
  │
  ▼
END (UpgradeReport 완성, Report Generator가 직렬화)
```

각 노드는 `backend/app/agents/`의 개별 함수/클래스이며, 상태는 하나의
LangGraph `State`(TypedDict/Pydantic)로 누적됩니다. 노드는 서로의 내부
구현이 아니라 State의 필드만 주고받습니다.

---

## 3. 컴포넌트별 책임

### 3.1 Collector 계층 (`backend/app/collectors/`)
클러스터에서 "사실"만 가져옵니다. 판단(compatibility, risk)은 하지 않습니다.

| 모듈 | 책임 |
|---|---|
| `kubernetes.py` | 버전, 노드 목록, 전 Namespace 리소스(Deploy/DS/STS/CRD/APIService 등) 조회. 동일 kubectl 호출 재사용을 위한 in-memory cache 보유 |
| `node.py` | OS/Kernel/cgroup/Container Runtime 정보 (node별), 값 불일치 감지용 raw 데이터 반환 |
| `etcd.py` | etcd manifest, member list, endpoint health, topology(stacked/external) 판단에 필요한 raw 데이터 |
| `addon.py` | 이미지 태그 파싱 → software/version 후보 추출 (판단은 Analyzer가 아니라 이 모듈이 "추론"까지 담당 — 순수 파싱 로직이므로 collector에 위치) |
| `manifest_scan.py` | Deprecated API 검사 대상 (kind, apiVersion) 수집: 라이브 오브젝트(workload/네트워킹/정책/웹훅 등) + `helm.sh/release.v1` Secret 을 디코드한 미적용 Helm 차트 매니페스트 |
| `pluto_scan.py` | 이미지에 구워넣은 pluto 바이너리로 `manifest_scan` 결과를 교차검증 (`pluto detect-files`, 클러스터 접근 없이 파일만; 데이터셋은 바이너리 내장이라 폐쇄망 OK) |

### 3.2 MCP 계층 (`backend/app/mcp/`)
- `client.py`: MCP Client 인터페이스 (`RealMCPClient` / `MockMCPClient`). Collector는 이 인터페이스만 알고 실제 구현을 모름.
- 도구 목록(`get_nodes`, `get_etcd_health` 등)은 kubectl-ai MCP Server 쪽 tool 이름과 1:1 매핑되는 얇은 wrapper.

### 3.3 Agent 계층 (`backend/app/agents/`)
| 모듈 | 책임 |
|---|---|
| `upgrade_agent.py` | LangGraph 그래프 정의/컴파일, 진입점 |
| `planner.py` | Upgrade Path 계산 + Version별 Plan(Pre/CP/Worker/Post) 조립 |
| `analyzer.py` | Cluster/CustomConfig/Software/Deprecated API 판단 로직 |
| `compatibility.py` | RAG 검색 결과 → CompatibilityResult 매핑, UNKNOWN 처리 |
| `risk.py` | 종합 Risk 산정 + Readiness Score 계산 |

### 3.4 RAG 계층 (`backend/app/rag/` + `rag/`)
- `retriever.py`: Vector DB 조회 인터페이스. 문서 추가만으로 검색 결과가 갱신되도록 코드에 문서 목록을 하드코딩하지 않음.
- `ingestion.py`: `rag/documents/**`의 신규/변경 문서를 임베딩하여 적재하는 배치 스크립트.
- `rag/documents/`: Release Notes, Compatibility Matrix, Deprecated/Removed API Guide, kubeadm Upgrade Guide 등 원문 저장소 (버전 관리 가능한 텍스트/마크다운).

### 3.5 Models (`backend/app/models/`)
Pydantic 도메인 모델 — Step 2에서 상세 설계. `cluster.py`, `upgrade.py`, `risk.py`로 분리.

### 3.6 API 계층 (`backend/app/api/`)
- `POST /api/v1/analysis`, `GET /api/v1/analysis/{id}`, `GET /api/v1/analysis/{id}/events` (SSE), `GET /api/v1/analysis/{id}/report`.
- kubeconfig는 요청 처리 동안만 메모리/임시파일로 보관, 분석 종료 즉시 파기.

### 3.7 Services (`backend/app/services/`)
분석 세션 상태 관리(진행률 이벤트 발행), Audit Log 기록, Snapshot 저장/조회 등 API와 Agent 사이의 조율 로직.

### 3.8 Frontend (`frontend/`)
- `pages/`: Cluster Connection, Cluster Analysis(진행 상태), Upgrade Report(Dashboard/Inventory/Software/Risk/Timeline 탭).
- `api/`: 백엔드 REST/SSE 클라이언트.
- 전체 UI 텍스트는 한국어 기본.

---

## 4. 디렉토리 구조 (스캐폴딩 완료 상태)

```text
v1/
├─ backend/
│  ├─ app/
│  │  ├─ api/            # FastAPI 라우터
│  │  ├─ agents/          # LangGraph 노드/그래프
│  │  ├─ collectors/       # Cluster 원시 데이터 수집
│  │  ├─ mcp/              # MCP Client (Real/Mock)
│  │  ├─ rag/              # Retriever/Ingestion
│  │  ├─ models/           # Pydantic 도메인 모델
│  │  ├─ services/         # 세션/오케스트레이션/Audit/Snapshot
│  │  ├─ prompts/          # LLM 프롬프트 템플릿
│  │  └─ core/             # 설정, 로깅(민감정보 마스킹 포함)
│  └─ tests/
├─ frontend/
│  └─ src/
│     ├─ pages/
│     ├─ components/
│     ├─ api/
│     ├─ hooks/
│     └─ types/
├─ rag/
│  ├─ documents/
│  │  ├─ release-notes/
│  │  ├─ compatibility-matrix/
│  │  ├─ deprecation-guides/
│  │  └─ kubeadm-guides/
│  └─ ingestion/
├─ docker/
│  ├─ backend/
│  ├─ frontend/
│  └─ mcp/
├─ docs/
│  └─ architecture.md   (본 문서)
└─ examples/
   └─ mock-cluster/     # Step 3/7에서 사용할 고정 Mock 데이터
```

`README.md`, `docker-compose.yml`, `.env.example`은 Step 5~7 진행 후
실제 실행 가능한 내용으로 채워집니다 (지금 빈 껍데기로 만들지 않음).

---

## 5. 다음 단계

Step 2: `backend/app/models/`에 Pydantic 도메인 모델(ClusterInfo, NodeInfo,
EtcdInfo, AddonInfo, CustomConfig, CompatibilityResult, RiskFinding,
UpgradeStep, UpgradePlan, RAGReference) 설계.
