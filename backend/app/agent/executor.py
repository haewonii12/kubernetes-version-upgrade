"""Executor — Task를 실제 Tool 실행으로 변환하는 순수 dispatch 계층 (Section 3).

도메인 로직을 전혀 갖지 않는다 — ToolRegistry에서 조회한 Tool을 호출할 뿐이다.
mutating Tool은 절대 실행하지 않고 ProposedAction으로 대체한다 (Section 8 Safety).
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import UTC, datetime

from app.agent.tools import ToolRegistry
from app.agent.tools.base import AgentTool, ToolContext
from app.models.agent import AgentEventType, Task, TaskStatus, ToolCallRecord, ToolResult
from app.models.agent_safety import ApprovalStatus, ProposedAction

EmitFn = Callable[[AgentEventType, dict], None]


class Executor:
    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry

    async def execute_batch(
        self, tasks: list[Task], ctx: ToolContext, emit: EmitFn
    ) -> list[tuple[Task, ToolResult]]:
        results: list[tuple[Task, ToolResult]] = []
        for task in tasks:
            if ctx.state.is_tool_call_guardrail_exceeded():
                ctx.state.mark_task_done(task.id, TaskStatus.SKIPPED)
                continue

            try:
                tool = self._resolve_tool(task)
            except ValueError as exc:
                ctx.state.mark_task_done(task.id, TaskStatus.FAILED)
                results.append((task, ToolResult(tool_name=task.tool_name or "?", ok=False, summary=str(exc), error=str(exc))))
                continue

            emit(AgentEventType.TOOL_SELECTED, {"task_id": task.id, "tool_name": tool.name})

            if tool.is_mutating:
                proposed = ProposedAction(
                    id=uuid.uuid4().hex[:12],
                    description=task.description,
                    verb="unknown",
                    approval_status=ApprovalStatus.PENDING,
                    created_at_iteration=ctx.state.iteration,
                )
                ctx.state.memory_working.setdefault("proposed_actions", []).append(proposed.model_dump(mode="json"))
                ctx.state.mark_task_done(task.id, TaskStatus.SKIPPED)
                continue

            started = datetime.now(UTC)
            emit(AgentEventType.TOOL_STARTED, {"task_id": task.id, "tool_name": tool.name})
            try:
                result = await tool.execute(task, ctx)
            except Exception as exc:  # noqa: BLE001 — Tool 실패는 run 전체를 죽이지 않는다
                result = ToolResult(tool_name=tool.name, ok=False, summary=f"Tool 실행 중 오류: {exc}", error=str(exc))

            record = ToolCallRecord(
                id=uuid.uuid4().hex[:12],
                task_id=task.id,
                tool_name=tool.name,
                started_at=started,
                finished_at=datetime.now(UTC),
                ok=result.ok,
                not_configured=result.not_configured,
                error=result.error,
            )
            ctx.state.record_tool_call(record)
            ctx.state.mark_task_done(task.id, TaskStatus.DONE if result.ok else TaskStatus.FAILED)
            emit(AgentEventType.TOOL_COMPLETED, {"task_id": task.id, "tool_name": tool.name, "ok": result.ok})
            results.append((task, result))

        return results

    def _resolve_tool(self, task: Task) -> AgentTool:
        if not task.tool_name or not self._registry.has(task.tool_name):
            raise ValueError(f"Task {task.id!r}가 실행 가능한 tool_name을 갖고 있지 않습니다: {task.tool_name!r}")
        return self._registry.get(task.tool_name)
