# Autonomous Agent Subsystem — Architecture (`agi` branch)

> 이 문서는 `agi` 브랜치에만 존재하는 서브시스템을 다룬다. `main`/`llm-agent`
> 브랜치의 고정 워크플로우는 [`docs/architecture.md`](architecture.md)를 그대로
> 따르며, 이 브랜치가 그 설계를 변경하거나 대체하지 않는다 — 완전히 별도의,
> 독립적으로 확장 가능한 서브시스템으로 추가되었다.

> **용어 주의**: 이 문서와 코드 전체에서 구현하는 것은 실제 AGI(Artificial
> General Intelligence)가 아니다. "Autonomous Agent", "Cognitive Agent",
> "Goal-driven Agent", "Generalist Infrastructure Agent" 라는 표현만 사용하며,
> 실제 AGI를 구현했다고 주장하지 않는다.

## 0. 설계 원칙

`docs/architecture.md`의 다섯 원칙(Read Only First, Evidence Based, No
Hallucination, DRY, Modular)을 그대로 계승하고, 두 가지를 추가한다.

| 원칙 | 의미 |
|---|---|
| Read Only First | (계승) Write 작업은 `ProposedAction`으로만 제안되고 절대 자동 실행되지 않는다 |
| Evidence Based | (계승) 모든 판단은 `Evidence`(source_type/title/url/retrieved_at)를 남긴다 |
| No Hallucination | (계승) 근거가 부족하면 `Critic`이 `insufficient`로 판단하고 재계획하거나, 가드레일에 걸리면 미해결 사항을 명시하고 끝난다 — 추측하지 않는다 |
| DRY | (계승) `agents/compatibility.py`, `agents/risk.py`, `agents/deprecated_api.py`, `collectors/*`를 재구현 없이 `AgentTool`로 wrap해 재사용한다 |
| Modular | (계승) GoalManager/Planner/Executor/Observer/Critic/ToolRegistry/Memory/Safety는 서로의 내부 구현을 몰라도 되게 인터페이스로만 통신한다 |
| 개방망 대응 | `main`/`llm-agent`가 폐쇄망(런타임 인터넷 호출 없음)을 전제로 하는 것과 반대로, 이 브랜치는 인터넷 접근이 가능함을 전제로 한다 — Web Search/공식 K8s 문서/GitHub를 실제로 호출하되, API 키/설정이 없으면 `LLMClient.is_configured`와 동일한 철학으로 조용히 `not_configured` fallback한다 |
| 용어 주의 | 코드/문서 어디에도 "AGI를 구현했다"는 표현을 쓰지 않는다 (위 안내 참고) |

## 1. 전체 아키텍처

```text
                    ┌──────────────────────────────┐
                    │   Knowledge (RAG, 계승)        │
                    │   rag/documents/**             │
                    └───────────────┬────────────────┘
                                    │ RAGRetriever
┌──────────┐  REST/SSE  ┌───────────▼────────────────────────────┐
│ Frontend │◄──────────►│  FastAPI Backend — /api/v1/agent/*      │
│ (React)  │            │  ┌────────────────────────────────────┐ │
└──────────┘            │  │           AgentRuntime              │ │
                         │  │  GoalManager → Planner → Executor   │ │
                         │  │       ↑         ↓          ↓        │ │
                         │  │     Critic ← Observer ← ToolRegistry│ │
                         │  └───────────────┬────────────────────┘ │
                         │                  │                       │
                         │  ┌───────────────▼────────────────────┐ │
                         │  │              Memory                 │ │
                         │  │  Working(run) / Episodic(past runs) │ │
                         │  │  / LongTerm(stub)                   │ │
                         │  └──────────────────────────────────────┘ │
                         └───────────────┬───────────────────────────┘
                                         │ ToolRegistry
              ┌──────────────────────────┼───────────────────────────┐
              │                          │                           │
   ┌──────────▼─────────┐   ┌────────────▼───────────┐   ┌───────────▼──────────┐
   │ Kubernetes MCP      │   │ Internal RAG            │   │ Open Network          │
   │ (재사용: Collector/  │   │ (재사용: RAGRetriever)   │   │ Web Search/공식문서/   │
   │  Compatibility/Risk/│   │                          │   │ GitHub (API 키 없으면  │
   │  DeprecatedApi)      │   │                          │   │  not_configured)      │
   └──────────┬───────────┘   └─────────────────────────┘   └───────────────────────┘
              │
   ┌──────────▼──────────┐
   │  Kubernetes Cluster  │
   └──────────────────────┘
```

Mock 모드는 기존과 동일하게 `MockMCPClient`(`examples/mock-cluster/`)로 전체
파이프라인을 오프라인으로 검증할 수 있다.

## 2. Cognitive Loop (LangGraph)

```text
START -> goal_manager -> planner -> executor -> observer -> critic
critic --[insufficient]--> planner   (재계획 루프)
critic --[sufficient / 가드레일 초과]--> finalizer -> END
```

LangGraph는 "문제 해결 절차"를 고정하지 않는다 — 이 6개 노드/엣지는 "인지
루프" 그 자체이고, Planner가 실제로 만드는 Task 종류만 Goal에 따라 동적으로
바뀐다.

- **executor** 노드는 그 tick의 PENDING Task 배치 전체를 한 번에 실행한다
  (Task 하나당 그래프를 한 바퀴 도는 게 아니다).
- **observer** 노드는 그 배치의 결과 전체를 한 번에 Observation으로 변환한다.
- 둘 사이는 `AgentState.memory_working["_last_batch_results"]`라는 하나의
  transient state 키로만 통신한다 — 숨은 Python 클로저로 데이터를 넘기지 않는다.
- 실행 중 새 정보가 발견되면(예: Calico 3.30.7) `observer`가
  `Observation.follow_up_hint`를 세우고, `critic`이 이를 이유로
  `insufficient`를 반환해 `planner`로 되돌아가며, `planner.replan()`이 그
  hint를 실제 Task로 변환한다 (`subject_key`로 중복 방지).
- `route_after_critic`은 `AgentState.is_guardrail_exceeded()`(iteration 또는
  tool_call 총량 초과)를 verdict보다 먼저 확인하므로, Critic이 계속
  insufficient를 반환해도 무한 루프에 빠지지 않고 `finalizer`로 빠진다.

## 3. AgentState

`backend/app/agent/state.py` — pydantic 모델. 모든 리스트/딕셔너리 변형은
아래 메서드를 통해서만 일어난다 (Node 함수가 직접 mutate하지 않는다):

`set_goal`, `add_task`(subject_key로 dedup), `pending_tasks`,
`pop_pending_batch`, `mark_task_done`, `add_observation`, `add_evidence`(dedup),
`record_tool_call`, `increment_iteration`, `is_guardrail_exceeded`,
`is_tool_call_guardrail_exceeded`, `finalize`.

## 4. Tool 추상화 / Registry / Retrieval

`AgentTool`(name, description, capabilities, `is_mutating`,
`async def execute(task, ctx) -> ToolResult`) — Executor는 이 인터페이스만
안다. `ToolRetriever`는 `RAGRetriever.search()`와 동일한 TF-IDF 코사인
유사도 방식으로 Goal/Task와 관련 있는 Tool만 골라낸다 — 모든 Tool 설명을
한꺼번에 LLM context에 넣지 않는다. **Planner가 `task.tool_name`을
ToolRetriever로 미리 확정**하고, Executor는 `registry.get(tool_name)` 조회만
한다 — 새 Tool을 추가할 때 건드릴 곳은 `tools/registry_builder.py` 한 곳뿐이다.

| Tool | 상태 | 비고 |
|---|---|---|
| `cluster_inspector` | 완전 구현 | `collectors/*` 재사용 |
| `compatibility_checker` | 완전 구현 | `agents/compatibility.py` 재사용, 무수정 |
| `deprecated_api_checker` | 완전 구현 | `agents/deprecated_api.py` + `pluto_scan.py` 재사용, 무수정 |
| `risk_analyzer` | 완전 구현 | `agents/risk.py` 재사용, 무수정 |
| `internal_rag_search` | 완전 구현 | `RAGRetriever.search()` 재사용 |
| `web_search` | 실제 호출 + graceful fallback | API 키 없으면 `not_configured` |
| `official_kubernetes_docs` | 실제 호출 + graceful fallback | `kubernetes.io` 도메인 allowlist |
| `github_search` | 실제 호출 + graceful fallback | 익명 호출 가능, 토큰 있으면 완화 |
| `prometheus`/`grafana`/`argocd`/`git` | 스텁 | 이번 pass 범위 밖 — 항상 `not_configured` |

## 5. Safety (Scaffolding)

```text
Proposed Action -> Risk Assessment -> Human Approval -> Execution
```

`Executor.execute_batch`는 `tool.is_mutating`을 확인해 mutating Tool은 절대
`execute()`를 호출하지 않고 `ProposedAction(approval_status=PENDING)`을
기록한 뒤 Task를 SKIPPED 처리한다. 이번 pass에는 mutating Tool이 하나도
등록되어 있지 않다 (분석/계획 생성까지만 구현). `PolicyGuard.assert_read_only`는
향후 mutating Tool 작성자를 위한 예약된 가드다.

## 6. Memory (Knowledge와 분리)

| | 위치 | 수명 |
|---|---|---|
| Knowledge | `RAGRetriever` (`rag/documents/**`) | 영구 (문서 기반) |
| Working Memory | `AgentState.memory_working` (`memory/working.py` wrapper) | 이번 run 동안 |
| Episodic Memory | `backend/var/agent_memory/episodes/{run_id}.json` | run마다 영구 저장 |
| Long-term Memory | `backend/var/agent_memory/longterm.json` (스텁) | 미사용 — 인터페이스만 |

## 7. API / SSE

내부 `AgentEventType`(goal_created, planning, task_created, tool_selected,
tool_started, tool_completed, observation_created, critic_started,
replanning, task_completed, goal_completed, error)은
`agent/events.py::map_internal_event_to_ui()`를 통해서만 UI 이벤트
(`AgentUIEvent`: stage/progress/message)로 변환된다 — `analysis_service.py`의
`_NODE_STAGE_MAP`과 동일한 역할.

| Method | Path | 설명 |
|---|---|---|
| POST | `/api/v1/agent/goals` | 자연어 목표로 새 실행 시작 |
| GET | `/api/v1/agent/goals/{run_id}` | 상태 조회 |
| GET | `/api/v1/agent/goals/{run_id}/events` | SSE 진행 스트림 |
| GET | `/api/v1/agent/goals/{run_id}/report` | 최종 `AgentReport` |
| GET | `/api/v1/agent/goals` | Episodic Memory 기반 과거 실행 목록 |

기존 `/api/v1/analysis*`는 이 서브시스템과 완전히 독립적이며 전혀 수정되지
않았다.

## 8. `main`/`llm-agent` 대비 비교

| | `main` / `llm-agent` | `agi` |
|---|---|---|
| 네트워크 전제 | 폐쇄망 (런타임 인터넷 호출 없음) | 개방망 (Web Search/공식문서/GitHub) |
| 실행 절차 | 고정 LangGraph 워크플로우 (10 노드 순차) | Goal 기반 동적 루프 (6 노드, Planner가 Task를 동적 생성) |
| 재계획 | 없음 (한 번 계획하면 끝까지 그대로) | 있음 (Critic insufficient -> Planner가 증분 재계획) |
| Tool 선택 | 없음 (모든 Node가 고정) | ToolRetriever가 Goal/Task 관련도로 동적 선택 |
| Write 작업 | 코드/RBAC 양쪽에서 차단 | 코드에서 차단 + `ProposedAction` 스캐폴딩 |
| 재사용 관계 | — | `agents/*.py`, `collectors/*.py`를 무수정 재사용 |

두 브랜치는 서로 독립적으로 발전할 수 있으며, 한쪽의 변경이 다른 쪽의 동작을
깨뜨리지 않는다.
