"""LLM이 RAG 판정 + Web/GitHub 근거를 종합해 Compatibility를 재검증/보강하는 경로.

RAG가 이미 판정한 버전도 웹 근거로 다시 확인하고(불일치 시 웹 근거 우선),
RAG에 아예 없는 버전(예: 최신 목표 버전)은 이 결과로 채워 넣는다.
"""

from __future__ import annotations

import json

import pytest

from app.agent.observer import Observer
from app.agent.planner import Planner
from app.agent.tools.compatibility_llm_verifier_tool import CompatibilityLlmVerifierTool
from app.models.agent import Task, ToolResult
from tests.conftest import FakeLLMClient


def _web_and_github_results_for_calico() -> list[tuple[Task, ToolResult]]:
    web_task = Task(
        id="w1", description="calico 웹 조사", tool_name="web_search",
        input={"query": "calico kubernetes 1.37 compatibility", "component": "calico", "target_version": "1.37"},
        subject_key="external_research:web_search:calico:1.37",
    )
    web_result = ToolResult(tool_name="web_search", ok=True, summary="검색 결과 1건", evidence=[])
    gh_task = Task(
        id="g1", description="calico GitHub 조사", tool_name="github_search",
        input={"query": "calico kubernetes 1.37 compatibility", "component": "calico", "target_version": "1.37"},
        subject_key="external_research:github_search:calico:1.37",
    )
    gh_result = ToolResult(tool_name="github_search", ok=True, summary="검색 결과 1건", evidence=[])
    return [(web_task, web_result), (gh_task, gh_result)]


def test_observer_flags_llm_verification_only_when_llm_configured(agent_state_factory):
    state = agent_state_factory(goal_text="1.37 업그레이드 분석", target_version="1.37")
    state.memory_working["compatibility_research_items"] = {
        "calico:1.37": {
            "component": "calico",
            "current_version": "3.30.7",
            "target_version": "1.37",
            "rag_judgments": [{"target_kubernetes_version": "1.36", "status": "COMPATIBLE", "reason": "..."}],
        }
    }
    results = _web_and_github_results_for_calico()

    # LLM 미설정: hint가 세워지지 않아야 한다.
    observer_no_llm = Observer(llm_client=None)
    observations = observer_no_llm.observe_batch(results, state)
    assert all(o.follow_up_hint is None or o.follow_up_hint.get("kind") != "llm_verify_compatibility" for o in observations)


def test_observer_flags_llm_verification_when_llm_configured(agent_state_factory):
    state = agent_state_factory(goal_text="1.37 업그레이드 분석", target_version="1.37")
    state.memory_working["compatibility_research_items"] = {
        "calico:1.37": {
            "component": "calico",
            "current_version": "3.30.7",
            "target_version": "1.37",
            "rag_judgments": [{"target_kubernetes_version": "1.36", "status": "COMPATIBLE", "reason": "..."}],
        }
    }
    results = _web_and_github_results_for_calico()

    observer = Observer(llm_client=FakeLLMClient(configured=True))
    observations = observer.observe_batch(results, state)

    hinted = [o for o in observations if o.follow_up_hint and o.follow_up_hint.get("kind") == "llm_verify_compatibility"]
    assert len(hinted) == 1
    hint = hinted[0].follow_up_hint
    assert hint["component"] == "calico"
    assert hint["verify_subject_key"] == "llm_verify_compatibility:calico:1.37"
    assert hint["rag_judgments"][0]["target_kubernetes_version"] == "1.36"


def test_planner_creates_verifier_task_from_hint(agent_state_factory, tool_retriever):
    state = agent_state_factory(goal_text="1.37 업그레이드 분석", target_version="1.37")
    state.memory_working["compatibility_research_items"] = {
        "calico:1.37": {"component": "calico", "current_version": "3.30.7", "target_version": "1.37", "rag_judgments": []}
    }
    results = _web_and_github_results_for_calico()
    observer = Observer(llm_client=FakeLLMClient(configured=True))
    observer.observe_batch(results, state)

    planner = Planner(tool_retriever, llm_client=None)
    new_tasks = planner.replan(state)
    added = [t for t in new_tasks if state.add_task(t)]

    verifier_tasks = [t for t in added if t.tool_name == "compatibility_llm_verifier"]
    assert len(verifier_tasks) == 1
    assert verifier_tasks[0].subject_key == "llm_verify_compatibility:calico:1.37"

    # idempotent: 다시 replan해도 중복 생성되지 않는다.
    assert [t for t in planner.replan(state) if state.add_task(t)] == []


@pytest.mark.asyncio
async def test_verifier_tool_fills_gap_and_overrides_rag(agent_state_factory, tool_context_factory):
    """RAG는 1.36만 알고(COMPATIBLE), 1.37은 RAG에 아예 없다.
    LLM이 웹 근거로 1.36은 뒤집고(WARNING) 1.37은 새로 채워 넣는다(INCOMPATIBLE)."""
    state = agent_state_factory(goal_text="1.37 업그레이드 분석", target_version="1.37")
    state.memory_working["compatibility_results"] = [
        {
            "component": "calico", "current_version": "3.30.7", "target_kubernetes_version": "1.36",
            "status": "COMPATIBLE", "reason": "RAG 문서 기준", "recommendation": None, "sources": [], "verified_by": "rag",
        }
    ]
    llm_response = json.dumps(
        {
            "judgments": [
                {"target_kubernetes_version": "1.36", "status": "WARNING", "reason": "웹 근거상 알려진 이슈 있음 — RAG와 다름"},
                {"target_kubernetes_version": "1.37", "status": "INCOMPATIBLE", "reason": "GitHub 이슈에서 확인됨"},
            ]
        }
    )
    llm = FakeLLMClient(configured=True, canned_response=llm_response)
    ctx = tool_context_factory(state, llm_client=llm)

    task = Task(
        id="v1", description="verify", tool_name="compatibility_llm_verifier",
        input={
            "component": "calico",
            "current_version": "3.30.7",
            "rag_judgments": [{"target_kubernetes_version": "1.36", "status": "COMPATIBLE", "reason": "RAG 문서 기준"}],
            "evidence": [{"source_type": "web_search", "title": "Calico known issue", "excerpt": "..."}],
        },
    )

    result = await CompatibilityLlmVerifierTool().execute(task, ctx)

    assert result.ok is True
    results_by_version = {r["target_kubernetes_version"]: r for r in state.memory_working["compatibility_results"]}
    assert len(results_by_version) == 2
    assert results_by_version["1.36"]["status"] == "WARNING"
    assert results_by_version["1.36"]["verified_by"] == "llm_web_search"
    assert results_by_version["1.37"]["status"] == "INCOMPATIBLE"
    assert results_by_version["1.37"]["verified_by"] == "llm_web_search"


@pytest.mark.asyncio
async def test_verifier_tool_not_configured_without_llm(agent_state_factory, tool_context_factory):
    state = agent_state_factory(goal_text="x")
    ctx = tool_context_factory(state, llm_client=None)
    task = Task(id="v1", description="verify", tool_name="compatibility_llm_verifier", input={"component": "calico", "evidence": [{}]})

    result = await CompatibilityLlmVerifierTool().execute(task, ctx)

    assert result.not_configured is True
    assert result.ok is False
