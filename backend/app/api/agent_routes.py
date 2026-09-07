"""자율 에이전트 REST + SSE API — 기존 ``/api/v1/analysis*`` 는 전혀 건드리지 않는다.

기존 ``api/routes.py`` 와 동일한 패턴(멀티파트 업로드, 0.2초 polling SSE, 409/500
상태 코드)을 그대로 따르되, 완전히 별도의 prefix(``/api/v1/agent``)와 세션
저장소(``agent_session_store``)를 쓴다.
"""

from __future__ import annotations

import asyncio
import uuid

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from sse_starlette.sse import EventSourceResponse

from app.agent.memory.episodic import EpisodicMemory
from app.core.config import settings
from app.services import agent_runtime_service
from app.services.agent_session_store import AgentRunSession, agent_session_store

router = APIRouter(prefix="/api/v1/agent")

_background_tasks: set[asyncio.Task] = set()


def _get_session_or_404(run_id: str) -> AgentRunSession:
    session = agent_session_store.get(run_id)
    if session is None:
        raise HTTPException(status_code=404, detail="해당 run_id를 찾을 수 없습니다.")
    return session


@router.post("/goals")
async def create_agent_goal(
    request: str = Form(...),
    target_kubernetes_version: str | None = Form(None),
    mock_mode: bool = Form(True),
    llm_endpoint: str | None = Form(None),
    llm_model: str | None = Form(None),
    kubeconfig: UploadFile | None = File(None),
) -> dict:
    session = agent_session_store.create(
        request,
        target_kubernetes_version or None,
        mock_mode,
        llm_endpoint=llm_endpoint or None,
        llm_model=llm_model or None,
    )

    kubeconfig_path = None
    if not mock_mode:
        if kubeconfig is None:
            raise HTTPException(status_code=400, detail="실제 클러스터 분석에는 kubeconfig 파일이 필요합니다.")
        settings.kubeconfig_tmp_dir.mkdir(parents=True, exist_ok=True)
        kubeconfig_path = settings.kubeconfig_tmp_dir / f"{session.run_id}-{uuid.uuid4().hex}.yaml"
        kubeconfig_path.write_bytes(await kubeconfig.read())

    task = asyncio.create_task(agent_runtime_service.run_agent(session, kubeconfig_path))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)

    return {"run_id": session.run_id}


@router.get("/goals/{run_id}")
async def get_agent_goal_status(run_id: str) -> dict:
    session = _get_session_or_404(run_id)
    latest = session.events[-1] if session.events else None
    return {
        "run_id": session.run_id,
        "status": session.status,
        "raw_request": session.raw_request,
        "target_version": session.target_version,
        "mock_mode": session.mock_mode,
        "latest_event": latest.model_dump() if latest else None,
        "error": session.error,
    }


@router.get("/goals/{run_id}/events")
async def stream_agent_goal_events(run_id: str) -> EventSourceResponse:
    session = _get_session_or_404(run_id)

    async def event_generator():
        sent = 0
        while True:
            while sent < len(session.events):
                event = session.events[sent]
                sent += 1
                yield {"data": event.model_dump_json()}
            if session.status != "RUNNING":
                return
            await asyncio.sleep(0.2)

    return EventSourceResponse(event_generator())


@router.get("/goals/{run_id}/report")
async def get_agent_goal_report(run_id: str) -> dict:
    session = _get_session_or_404(run_id)
    if session.status == "RUNNING":
        raise HTTPException(status_code=409, detail="아직 실행 중입니다.")
    if session.status == "FAILED":
        raise HTTPException(status_code=500, detail=f"실행이 실패했습니다: {session.error}")
    assert session.report is not None
    return session.report.model_dump(mode="json")


@router.get("/goals")
async def list_agent_goals() -> list[dict]:
    """Section 7 Episodic Memory: 과거 실행 기록 목록."""
    return EpisodicMemory(settings.agent_memory_dir).list_recent()
