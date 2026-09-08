"""자율 에이전트 실행 orchestration — services/analysis_service.py 의 새 워크플로우 버전.

기존 ``run_analysis`` 와 달리 이 함수는 async-native다: AgentTool.execute가 이미
async이므로(오픈 네트워크 Tool은 httpx 비동기 호출, MCP/RAG 기반 Tool은 내부에서
``anyio.to_thread.run_sync`` 로 스레드로 넘긴다) 그래프 실행 자체를 스레드로 감쌀
필요가 없다. API 계층에서 ``asyncio.create_task(run_agent(...))`` 로 직접 스폰한다.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path

import anyio

from app.agent.events import map_internal_event_to_ui
from app.agent.memory.episodic import EpisodicMemory
from app.agent.runtime import build_agent_runtime
from app.agent.state import AgentState
from app.agent.tools.registry_builder import build_default_registry
from app.core.config import settings
from app.core.logging import get_audit_logger
from app.llm.client import LLMClient
from app.mcp.client import create_mcp_client
from app.models.agent import AgentEvent, AgentReport
from app.services import analysis_service
from app.services.agent_session_store import AgentRunSession

logger = logging.getLogger(__name__)


async def run_agent(session: AgentRunSession, kubeconfig_path: Path | None) -> None:
    audit_logger = get_audit_logger(settings.audit_log_path)
    audit_logger.info("agent_run_id=%s action=start target_version=%s mock_mode=%s", session.run_id, session.target_version, session.mock_mode)

    client = None
    try:
        if session.mock_mode:
            client = await anyio.to_thread.run_sync(
                lambda: create_mcp_client("mock", fixture_dir=analysis_service.MOCK_FIXTURE_DIR)
            )
        else:
            client = await anyio.to_thread.run_sync(
                lambda: create_mcp_client(
                    "stdio",
                    server_command=settings.mcp_server_command,
                    server_args=settings.mcp_server_args.split(),
                    kubeconfig_path=kubeconfig_path,
                )
            )

        rag = analysis_service.get_rag()
        llm_client = (
            LLMClient(session.llm_endpoint, session.llm_model, api_key=settings.llm_api_key)
            if session.llm_endpoint and session.llm_model
            else None
        )
        registry = build_default_registry(settings=settings)
        runtime = build_agent_runtime(mcp_client=client, rag=rag, llm_client=llm_client, registry=registry, settings=settings)

        state = AgentState(
            run_id=session.run_id,
            raw_request=session.raw_request,
            goal_target_version_hint=session.target_version,
            mock_mode=session.mock_mode,
            max_iterations=settings.agent_max_iterations,
            max_tool_calls=settings.agent_max_tool_calls,
        )

        def _on_event(event: AgentEvent) -> None:
            ui_event = map_internal_event_to_ui(event, state)
            session.emit(ui_event)
            audit_logger.info("agent_run_id=%s event=%s message=%s", session.run_id, event.type.value, event.message)

        graph = runtime.build_graph(_on_event)
        result = await graph.ainvoke({"agent_state": state})
        final_state: AgentState = result["agent_state"]
        assert final_state.final_conclusion is not None

        report = AgentReport(
            run_id=session.run_id,
            created_at=datetime.now(UTC),
            goal=final_state.goal,
            plan_history=final_state.plan,
            observations=final_state.observations,
            tool_calls=final_state.tool_calls,
            final_conclusion=final_state.final_conclusion,
            proposed_actions=final_state.memory_working.get("proposed_actions", []),
        )
        session.report = report
        session.status = "COMPLETED"
        EpisodicMemory(settings.agent_memory_dir).save_run(report)
        audit_logger.info("agent_run_id=%s action=run result=SUCCESS goal_met=%s", session.run_id, report.final_conclusion.goal_met)
    except Exception as exc:  # noqa: BLE001
        logger.exception("agent run failed: run_id=%s", session.run_id)
        session.status = "FAILED"
        session.error = str(exc)
        audit_logger.info("agent_run_id=%s action=run result=FAILED error=%s", session.run_id, exc)
    finally:
        if client is not None:
            await anyio.to_thread.run_sync(client.close)
        if kubeconfig_path and kubeconfig_path.exists():
            kubeconfig_path.unlink()
            audit_logger.info("agent_run_id=%s action=kubeconfig_cleanup result=SUCCESS", session.run_id)
