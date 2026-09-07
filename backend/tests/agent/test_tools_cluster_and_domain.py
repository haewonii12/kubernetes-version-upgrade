"""기존 도메인 로직(agents/compatibility.py 등)이 재구현이 아니라 그대로 wrap되는지 확인."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.agents import compatibility as compatibility_module
from app.agent.tools.cluster_tools import ClusterInspectorTool
from app.agent.tools.compatibility_tool import CompatibilityCheckerTool
from app.agent.tools.risk_tool import RiskAnalyzerTool
from app.models.agent import Task


@pytest.mark.asyncio
async def test_cluster_inspector_populates_working_memory(agent_state_factory, tool_context_factory):
    state = agent_state_factory(goal_text="inspect")
    ctx = tool_context_factory(state)

    result = await ClusterInspectorTool().execute(Task(id="1", description="inspect"), ctx)

    assert result.ok is True
    assert state.memory_working["cluster"]["kubernetes_version"] == "1.32.13"
    assert state.cluster_current_version == "1.32.13"


@pytest.mark.asyncio
async def test_compatibility_checker_calls_existing_pure_function_unmodified(agent_state_factory, tool_context_factory):
    state = agent_state_factory(goal_text="check", target_version="1.36")
    ctx = tool_context_factory(state)
    await ClusterInspectorTool().execute(Task(id="1", description="inspect"), ctx)

    with patch(
        "app.agent.tools.compatibility_tool.evaluate_compatibility", wraps=compatibility_module.evaluate_compatibility
    ) as spy:
        result = await CompatibilityCheckerTool().execute(
            Task(id="2", description="compat", input={"target_version": "1.36"}), ctx
        )
        assert spy.called

    assert result.ok is True
    assert "compatibility_results" in state.memory_working


@pytest.mark.asyncio
async def test_compatibility_checker_fails_gracefully_without_cluster_data(agent_state_factory, tool_context_factory):
    state = agent_state_factory(goal_text="check", target_version="1.36")
    ctx = tool_context_factory(state)

    result = await CompatibilityCheckerTool().execute(Task(id="1", description="compat"), ctx)

    assert result.ok is False
    assert result.error == "missing_cluster"


@pytest.mark.asyncio
async def test_risk_analyzer_requires_prerequisite_data(agent_state_factory, tool_context_factory):
    state = agent_state_factory(goal_text="risk")
    ctx = tool_context_factory(state)

    result = await RiskAnalyzerTool().execute(Task(id="1", description="risk"), ctx)

    assert result.ok is False
    assert result.error == "missing_cluster"
