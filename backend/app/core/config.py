from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_ROOT.parent


class Settings(BaseSettings):
    """런타임 설정. 모두 환경변수로 override 가능 (.env.example 참고)."""

    model_config = SettingsConfigDict(env_prefix="UPGRADE_AGENT_", env_file=".env", extra="ignore")

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

    # --- Autonomous Agent (agi 브랜치, Section 6/8/10) ---
    # Open Network 사용 여부 스위치. False면 WebSearch/공식문서/GitHub Tool이 모두
    # not_configured 로 graceful fallback한다 (LLMClient.is_configured와 동일 철학).
    agent_open_network_enabled: bool = False
    agent_web_search_api_key: str | None = None
    agent_web_search_endpoint: str = "https://api.search.brave.com/res/v1/web/search"
    agent_github_token: str | None = None
    agent_prometheus_endpoint: str | None = None
    agent_grafana_endpoint: str | None = None
    agent_argocd_endpoint: str | None = None
    agent_max_iterations: int = 6
    agent_max_tool_calls: int = 30
    agent_memory_dir: Path = PROJECT_ROOT / "backend" / "var" / "agent_memory"


settings = Settings()
