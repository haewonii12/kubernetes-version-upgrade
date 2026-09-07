"""AgentState: 자율 루프 전체가 공유하는 단일 상태 (Section 10).

모든 리스트/딕셔너리 변형은 이 클래스의 메서드를 통해서만 일어난다 — LangGraph 노드
함수들은 ``state.plan.append(...)`` 처럼 직접 건드리지 않는다 (임의 dict 변형 방지 요구사항).
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.agent import (
    Evidence,
    FinalConclusion,
    Goal,
    Observation,
    Task,
    TaskStatus,
    ToolCallRecord,
)


class AgentStatus(str, Enum):
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    MAX_ITERATIONS_REACHED = "MAX_ITERATIONS_REACHED"


class AgentState(BaseModel):
    """단일 실행(run)의 진실의 원천. WorkingMemory는 이 객체의 ``memory_working`` 을 감싸는 얇은 wrapper다."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    run_id: str
    raw_request: str = ""
    goal_target_version_hint: str | None = None
    mock_mode: bool = True
    goal: Goal | None = None
    cluster_current_version: str | None = None

    plan: list[Task] = Field(default_factory=list)
    observations: list[Observation] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    memory_working: dict[str, Any] = Field(default_factory=dict)

    iteration: int = 0
    max_iterations: int = 6
    max_tool_calls: int = 30
    planner_exhausted: bool = False

    status: AgentStatus = AgentStatus.RUNNING
    final_conclusion: FinalConclusion | None = None

    # ---- 중앙 집중식 변형 메서드 ----

    def set_goal(self, goal: Goal) -> None:
        self.goal = goal
        if goal.target_version:
            self.goal_target_version_hint = goal.target_version

    def add_task(self, task: Task) -> bool:
        """subject_key가 이미 존재하는 Task와 겹치면 추가하지 않는다 (replan 시 중복 방지)."""
        if task.subject_key is not None and any(t.subject_key == task.subject_key for t in self.plan):
            return False
        self.plan.append(task)
        return True

    def pending_tasks(self) -> list[Task]:
        return [t for t in self.plan if t.status == TaskStatus.PENDING]

    def pop_pending_batch(self) -> list[Task]:
        """현재 PENDING인 Task를 모두 RUNNING으로 표시하고 반환한다 (이번 tick의 Executor 배치)."""
        batch = self.pending_tasks()
        for task in batch:
            task.status = TaskStatus.RUNNING
        return batch

    def mark_task_done(self, task_id: str, status: TaskStatus = TaskStatus.DONE) -> None:
        for task in self.plan:
            if task.id == task_id:
                task.status = status
                return

    def add_observation(self, observation: Observation) -> None:
        self.observations.append(observation)

    def add_evidence(self, evidence: list[Evidence]) -> None:
        existing = {(e.source_type, e.title, e.url, e.doc_id) for e in self.evidence}
        for ev in evidence:
            key = (ev.source_type, ev.title, ev.url, ev.doc_id)
            if key not in existing:
                existing.add(key)
                self.evidence.append(ev)

    def record_tool_call(self, record: ToolCallRecord) -> None:
        self.tool_calls.append(record)

    def increment_iteration(self) -> None:
        self.iteration += 1

    def is_guardrail_exceeded(self) -> bool:
        """반복(iteration) 라운드 진입을 막을지 판단 — critic 이후 라우팅에서만 쓴다."""
        return self.iteration >= self.max_iterations or self.is_tool_call_guardrail_exceeded()

    def is_tool_call_guardrail_exceeded(self) -> bool:
        """Tool 호출 총량 한도. Executor가 배치 중간에 중단할지 판단할 때 쓴다 —
        iteration 한도까지 함께 검사하면 '이번 라운드는 이미 허가됐는데 방금 iteration
        카운터가 올라갔다는 이유만으로 배치를 하나도 실행 못 하는' 오작동이 생긴다."""
        return len(self.tool_calls) >= self.max_tool_calls

    def finalize(self, conclusion: FinalConclusion, status: AgentStatus) -> None:
        self.final_conclusion = conclusion
        self.status = status
