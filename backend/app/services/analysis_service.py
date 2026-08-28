"""분석 실행 orchestration: LangGraph Agent 구동 → 진행 이벤트 발행 → Report 조립.

API 계층은 이 모듈의 ``run_analysis``만 호출한다. Agent(``app.agents``)는 이
모듈의 존재를 모른다 — 진행 이벤트는 LangGraph의 ``stream()`` 출력(어떤 Node가
끝났는지)만 보고 매핑하므로, Agent Node를 추가/변경해도 이 파일을 고치지 않는 한
자동으로는 새 이벤트가 나오지 않는다는 점만 유의하면 된다(신규 Node 추가 시
``_NODE_STAGE_MAP``에 매핑을 추가한다).
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from app.agents.upgrade_agent import NODE_PROGRESS_MESSAGES, build_graph
from app.core.config import settings
from app.core.logging import get_audit_logger
from app.llm.client import LLMClient
from app.mcp.client import create_mcp_client
from app.models.report import AnalysisStage, UpgradeReport
from app.models.risk import ReadinessScore, RiskFinding, RiskSeverity
from app.models.upgrade import UpgradePlan
from app.rag.retriever import RAGRetriever
from app.services.session_store import AnalysisSession

logger = logging.getLogger(__name__)

MOCK_FIXTURE_DIR = Path(__file__).resolve().parents[3] / "examples" / "mock-cluster"

_NODE_STAGE_MAP: dict[str, AnalysisStage] = {
    "collect_cluster": AnalysisStage.NODE_SCAN,
    "analyze_cluster": AnalysisStage.OS_KERNEL_SCAN,
    "detect_custom_config": AnalysisStage.CUSTOM_CONFIG_SCAN,
    "detect_installed_software": AnalysisStage.ADDON_SCAN,
    "search_rag": AnalysisStage.RAG_SEARCH,
    "check_compatibility": AnalysisStage.COMPATIBILITY_CHECK,
    "check_deprecated_api": AnalysisStage.DEPRECATED_API_CHECK,
    "analyze_risk": AnalysisStage.RISK_ANALYSIS,
    "generate_upgrade_path": AnalysisStage.UPGRADE_PATH_GENERATION,
    "generate_upgrade_plan": AnalysisStage.UPGRADE_PLAN_GENERATION,
}
_NODE_ORDER = list(_NODE_STAGE_MAP.keys())

_rag_singleton: RAGRetriever | None = None


def get_rag() -> RAGRetriever:
    global _rag_singleton
    if _rag_singleton is None:
        _rag_singleton = RAGRetriever(settings.rag_documents_dir)
    return _rag_singleton


def run_analysis(session: AnalysisSession, kubeconfig_path: Path | None) -> None:
    """동기 함수. API 계층에서 ``asyncio.to_thread`` 로 호출한다."""
    audit_logger = get_audit_logger(settings.audit_log_path)
    audit_logger.info(
        "analysis_id=%s action=start target_version=%s mock_mode=%s",
        session.analysis_id, session.target_version, session.mock_mode,
    )
    session.emit(AnalysisStage.CLUSTER_CONNECTION, "클러스터 연결 중", 5)

    client = None
    try:
        if session.mock_mode:
            client = create_mcp_client("mock", fixture_dir=MOCK_FIXTURE_DIR)
        else:
            client = create_mcp_client(
                "stdio",
                server_command=settings.mcp_server_command,
                server_args=settings.mcp_server_args.split(),
                kubeconfig_path=kubeconfig_path,
            )

        rag = get_rag()
        llm_client = None
        if session.llm_endpoint and session.llm_model:
            llm_client = LLMClient(session.llm_endpoint, session.llm_model)
        graph = build_graph(client, rag, llm_client=llm_client)

        total = len(_NODE_ORDER)
        final_state: dict = {}
        for step in graph.stream({"target_version": session.target_version}, stream_mode="updates"):
            for node_name, update in step.items():
                final_state.update(update)
                stage = _NODE_STAGE_MAP.get(node_name)
                if stage is None:
                    continue
                idx = _NODE_ORDER.index(node_name)
                progress = int(10 + (idx + 1) / total * 85)
                message = NODE_PROGRESS_MESSAGES.get(node_name, node_name)
                session.emit(stage, message, progress)
                audit_logger.info("analysis_id=%s action=%s result=SUCCESS", session.analysis_id, node_name)

        executive_summary = _build_executive_summary(
            llm_client, final_state["readiness"], final_state["risks"], final_state["upgrade_plan"]
        )
        report = UpgradeReport(
            analysis_id=session.analysis_id,
            created_at=datetime.now(UTC),
            cluster=final_state["cluster"],
            readiness=final_state["readiness"],
            risks=final_state["risks"],
            upgrade_plan=final_state["upgrade_plan"],
            software_compatibility=final_state["compatibility_summary"],
            deprecated_apis=final_state["deprecated_summary"],
            deprecated_api_pluto_skipped=final_state.get("pluto_skip_reason"),
            executive_summary=executive_summary,
        )
        session.report = report
        session.status = "COMPLETED"
        session.emit(AnalysisStage.COMPLETED, "분석이 완료되었습니다", 100)
        _save_snapshot(report)
    except Exception as exc:  # noqa: BLE001
        logger.exception("analysis failed: analysis_id=%s", session.analysis_id)
        session.status = "FAILED"
        session.error = str(exc)
        session.emit(AnalysisStage.FAILED, f"분석 실패: {exc}", 100)
        audit_logger.info("analysis_id=%s action=analysis result=FAILED", session.analysis_id)
    finally:
        if client is not None:
            client.close()
        if kubeconfig_path and kubeconfig_path.exists():
            kubeconfig_path.unlink()
            audit_logger.info("analysis_id=%s action=kubeconfig_cleanup result=SUCCESS", session.analysis_id)


def _build_executive_summary(
    llm_client: LLMClient | None,
    readiness: ReadinessScore,
    risks: list[RiskFinding],
    upgrade_plan: UpgradePlan,
) -> str | None:
    """LLM이 설정된 경우에만 전체 리포트 상단에 노출할 요약 1개를 생성한다.

    Compatibility/Risk 판정 자체를 다시 계산하지 않는다 — 이미 확정된 구조화된
    결과(readiness, risks, upgrade_path)를 자연어로 서술만 한다. LLM이 없거나
    실패하면 ``None`` 을 반환하고, 이 경우 리포트에는 이 섹션 자체가 없다
    (프론트에서 필드가 없으면 안 보여줌 — 회귀 없음).
    """
    if llm_client is None or not llm_client.is_configured:
        return None

    top_risks = sorted(risks, key=lambda r: list(RiskSeverity).index(r.severity))[:5]
    context_lines = [
        f"업그레이드 준비 복잡도: {readiness.complexity}% (0=단순, 100=매우 복잡)",
        f"BLOCKER {readiness.blocker_count}건, HIGH {readiness.high_count}건, "
        f"MEDIUM {readiness.medium_count}건, LOW {readiness.low_count}건",
        f"Upgrade Path: {' -> '.join(upgrade_plan.upgrade_path)}",
        "주요 Risk:",
    ]
    context_lines += [f"- [{r.severity.value}] {r.finding}" for r in top_risks]
    context = "\n".join(context_lines)

    return llm_client.summarize(
        "위 정보를 바탕으로 이번 Kubernetes 업그레이드 전체를 3~4문장으로 요약해줘. "
        "가장 중요한 위험 요소를 반드시 언급해줘.",
        context,
    )


def _save_snapshot(report: UpgradeReport) -> None:
    settings.snapshot_dir.mkdir(parents=True, exist_ok=True)
    path = settings.snapshot_dir / f"{report.analysis_id}.json"
    path.write_text(report.model_dump_json(indent=2), encoding="utf-8")


def load_snapshot(analysis_id: str) -> UpgradeReport | None:
    path = settings.snapshot_dir / f"{analysis_id}.json"
    if not path.exists():
        return None
    return UpgradeReport.model_validate(json.loads(path.read_text(encoding="utf-8")))


def list_snapshots() -> list[dict]:
    if not settings.snapshot_dir.exists():
        return []
    result = []
    for path in sorted(settings.snapshot_dir.glob("*.json"), reverse=True):
        data = json.loads(path.read_text(encoding="utf-8"))
        result.append(
            {
                "analysis_id": data["analysis_id"],
                "created_at": data["created_at"],
                "kubernetes_version": data["cluster"]["kubernetes_version"],
                "target_version": data["upgrade_plan"]["target_version"],
                "readiness_score": data["readiness"]["score"],
            }
        )
    return result
