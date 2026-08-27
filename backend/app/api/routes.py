"""REST + SSE API (Section 5 Step5, Section 18).

kubeconfig 보안(Section 29): 업로드된 파일은 ``settings.kubeconfig_tmp_dir`` 에
분석 세션 동안만 저장되고, ``analysis_service.run_analysis`` 가 완료/실패 직후
반드시 삭제한다. 이 파일은 kubeconfig 자체를 로그로 남기지 않는다.
"""

from __future__ import annotations

import asyncio
import uuid

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from sse_starlette.sse import EventSourceResponse

from app.core.config import settings
from app.services import analysis_service
from app.services.session_store import AnalysisSession, session_store

router = APIRouter(prefix="/api/v1")

_background_tasks: set[asyncio.Task] = set()


@router.get("/target-versions")
async def list_target_versions() -> dict:
    """Section 18 UI의 Target Version 드롭다운 목록.

    ``rag/documents/release-notes/`` 에 존재하는 minor 버전만 반환한다 (하드코딩
    아님) — 새 Release Note 문서를 추가하면 백엔드 재기동만으로 자동 반영된다.
    """
    versions = analysis_service.get_rag().list_target_kubernetes_versions()
    return {"versions": versions}


def _get_session_or_404(analysis_id: str) -> AnalysisSession:
    session = session_store.get(analysis_id)
    if session is None:
        raise HTTPException(status_code=404, detail="해당 analysis_id를 찾을 수 없습니다.")
    return session


@router.post("/analysis")
async def create_analysis(
    target_kubernetes_version: str = Form(...),
    mock_mode: bool = Form(False),
    llm_endpoint: str | None = Form(None),
    llm_model: str | None = Form(None),
    kubeconfig: UploadFile | None = File(None),
) -> dict:
    session = session_store.create(
        target_kubernetes_version,
        mock_mode,
        llm_endpoint=llm_endpoint or None,
        llm_model=llm_model or None,
    )

    kubeconfig_path = None
    if not mock_mode:
        if kubeconfig is None:
            raise HTTPException(status_code=400, detail="실제 클러스터 분석에는 kubeconfig 파일이 필요합니다.")
        settings.kubeconfig_tmp_dir.mkdir(parents=True, exist_ok=True)
        kubeconfig_path = settings.kubeconfig_tmp_dir / f"{session.analysis_id}-{uuid.uuid4().hex}.yaml"
        kubeconfig_path.write_bytes(await kubeconfig.read())

    task = asyncio.create_task(asyncio.to_thread(analysis_service.run_analysis, session, kubeconfig_path))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)

    return {"analysis_id": session.analysis_id}


@router.get("/analysis/{analysis_id}")
async def get_analysis_status(analysis_id: str) -> dict:
    session = _get_session_or_404(analysis_id)
    latest = session.events[-1] if session.events else None
    return {
        "analysis_id": session.analysis_id,
        "status": session.status,
        "target_version": session.target_version,
        "mock_mode": session.mock_mode,
        "latest_event": latest.model_dump() if latest else None,
        "error": session.error,
    }


@router.get("/analysis/{analysis_id}/events")
async def stream_analysis_events(analysis_id: str) -> EventSourceResponse:
    session = _get_session_or_404(analysis_id)

    async def event_generator():
        sent = 0
        while True:
            while sent < len(session.events):
                event = session.events[sent]
                sent += 1
                # event 이름을 지정하지 않아 브라우저 EventSource의 기본 "message" 로 수신된다
                # (stage 값은 data JSON 안에 이미 포함되어 있음).
                yield {"data": event.model_dump_json()}
            if session.status != "RUNNING":
                return
            await asyncio.sleep(0.2)

    return EventSourceResponse(event_generator())


@router.get("/analysis/{analysis_id}/report")
async def get_analysis_report(analysis_id: str) -> dict:
    session = _get_session_or_404(analysis_id)
    if session.status == "RUNNING":
        raise HTTPException(status_code=409, detail="분석이 아직 진행 중입니다.")
    if session.status == "FAILED":
        raise HTTPException(status_code=500, detail=f"분석이 실패했습니다: {session.error}")
    assert session.report is not None
    return session.report.model_dump(mode="json")


@router.get("/snapshots")
async def list_snapshots() -> list[dict]:
    """Section 32: 과거 분석 결과 목록 (같은 클러스터의 변경 추이 비교용)."""
    return analysis_service.list_snapshots()


@router.get("/snapshots/{analysis_id}")
async def get_snapshot(analysis_id: str) -> dict:
    report = analysis_service.load_snapshot(analysis_id)
    if report is None:
        raise HTTPException(status_code=404, detail="해당 Snapshot을 찾을 수 없습니다.")
    return report.model_dump(mode="json")
