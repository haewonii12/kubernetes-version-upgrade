from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_ROOT.parent


class Settings(BaseSettings):
    """런타임 설정. 모두 환경변수로 override 가능 (.env.example 참고)."""

    # env_file은 절대경로로 고정한다 — 상대경로(".env")였다면 프로세스를 어느
    # 디렉터리에서 실행했는지에 따라 조용히 못 찾고 전부 기본값으로 fallback되는
    # 사고가 날 수 있다 (실제로 겪음: backend/가 아닌 곳에서 기동했더니 에러 없이
    # OpenRouter/OpenNetwork 설정이 통째로 무시됨).
    model_config = SettingsConfigDict(env_prefix="UPGRADE_AGENT_", env_file=str(BACKEND_ROOT / ".env"), extra="ignore")

    # 실제 클러스터 분석(mock_mode=false) 시 kubectl-ai MCP 서버를 하위 프로세스로
    # 기동하는 명령. mock/real 여부 자체는 분석 요청마다 mock_mode 파라미터로 결정된다.
    mcp_server_command: str = "kubectl-ai"
    mcp_server_args: str = "--mcp-server"

    # Deprecated API 교차검증용 pluto 바이너리 (Docker 이미지에 구워져 있음).
    # 없으면 pluto 스캔 단계는 조용히 건너뛴다 (RAG 판정은 그대로 동작).
    pluto_command: str = "pluto"

    # RAG
    rag_documents_dir: Path = PROJECT_ROOT / "rag" / "documents"
    rag_index_path: Path = PROJECT_ROOT / "rag" / "index" / "index.json"

    # kubeconfig 임시 저장 (분석 종료 후 즉시 삭제)
    kubeconfig_tmp_dir: Path = Path("/tmp/k8s-upgrade-agent/kubeconfig")

    # Audit log (credential/secret 값은 절대 기록하지 않음)
    audit_log_path: Path = PROJECT_ROOT / "backend" / "var" / "audit.log"

    # Cluster Snapshot (Section 32) — 분석 시점 UpgradeReport 전체를 저장해 추후 비교 가능
    snapshot_dir: Path = PROJECT_ROOT / "backend" / "var" / "snapshots"

    cors_allow_origins: list[str] = ["http://localhost:3000"]

    # LLM Endpoint/Model은 요청마다 UI에서 받지만(analysis_service.py,
    # agent_runtime_service.py), API 키는 브라우저를 거치지 않고 백엔드에만
    # 설정한다. OpenRouter처럼 인증이 필요한 서버를 쓸 때 여기에 넣는다
    # (endpoint=https://openrouter.ai/api/v1, model=예: openai/gpt-4o-mini).
    llm_api_key: str | None = None
    # UI에서 LLM Endpoint/Model을 비워두고 제출하면 이 기본값을 쓴다 — 매 요청마다
    # 똑같은 값을 타이핑해야 하는 번거로움 때문에 실수로 LLM 없이 제출되는 경우가
    # 많아서 추가했다 (그러면 agi 에이전트의 LLM 재검증 단계가 조용히 통째로
    # 꺼진다). 여전히 요청에서 직접 입력하면 그 값이 우선한다.
    llm_default_endpoint: str | None = None
    llm_default_model: str | None = None

    # --- Autonomous Agent (agi 브랜치, Section 6/8/10) ---
    # Open Network 사용 여부 스위치. False면 WebSearch/공식문서/GitHub Tool이 모두
    # not_configured 로 graceful fallback한다 (LLMClient.is_configured와 동일 철학).
    agent_open_network_enabled: bool = False
    agent_web_search_api_key: str | None = None
    agent_web_search_endpoint: str = "https://api.tavily.com/search"
    agent_github_token: str | None = None
    agent_prometheus_endpoint: str | None = None
    agent_grafana_endpoint: str | None = None
    agent_argocd_endpoint: str | None = None
    agent_max_iterations: int = 6
    agent_max_tool_calls: int = 30
    agent_memory_dir: Path = PROJECT_ROOT / "backend" / "var" / "agent_memory"


settings = Settings()
