"""AgentRuntime — 6-노드 Cognitive Loop LangGraph (Section 11).

    START -> goal_manager -> planner -> executor -> observer -> critic
    critic --[insufficient]--> planner   (loop)
    critic --[sufficient / guardrail 초과]--> finalizer -> END

LangGraph는 "문제 해결 절차"를 고정하지 않는다 — Planner가 만드는 실제 Task
종류만 동적으로 바뀌고, 그래프 자체(6개 노드/엣지)는 고정된 인지 루프다.
Executor 노드는 그 tick의 PENDING Task 배치 전체를 한 번에 실행하고, Observer
노드가 배치 전체를 한 번에 관찰로 변환한다 — 둘 사이는 ``AgentState`` 하나로만
통신한다 (숨은 클로저 없음).
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.agent.critic import Critic
from app.agent.executor import Executor
from app.agent.goal_manager import GoalManager
from app.agent.observer import Observer
from app.agent.planner import Planner
from app.agent.state import AgentState, AgentStatus
from app.agent.tools import ToolRegistry, ToolRetriever
from app.agent.tools.base import ToolContext
from app.core.config import Settings
from app.llm.client import LLMClient
from app.mcp.client import MCPClient
from app.models.agent import AgentEvent, AgentEventType, CriticVerdict, FinalConclusion
from app.rag.retriever import RAGRetriever

EmitFn = Callable[[AgentEvent], None]


class GraphState(TypedDict):
    agent_state: AgentState


class AgentRuntime:
    def __init__(
        self,
        *,
        mcp_client: MCPClient,
        rag: RAGRetriever,
        llm_client: LLMClient | None,
        registry: ToolRegistry,
        settings: Settings,
    ) -> None:
        tool_retriever = ToolRetriever(registry)
        self.goal_manager = GoalManager(llm_client)
        self.planner = Planner(tool_retriever, llm_client)
        self.executor = Executor(registry)
        self.observer = Observer(llm_client)
        self.critic = Critic(llm_client)
        self._llm_client = llm_client
        self._ctx_kwargs = {"mcp_client": mcp_client, "rag": rag, "llm_client": llm_client, "settings": settings}

    def build_graph(self, emit: EmitFn):
        def _ctx(state: AgentState) -> ToolContext:
            return ToolContext(state=state, **self._ctx_kwargs)

        def _emit(ev_type: AgentEventType, message: str, state: AgentState, **payload) -> None:
            emit(
                AgentEvent(
                    type=ev_type,
                    message=message,
                    timestamp=datetime.now(UTC),
                    iteration=state.iteration,
                    payload=payload,
                )
            )

        def goal_manager_node(g: GraphState) -> dict:
            state = g["agent_state"]
            goal = self.goal_manager.parse_goal(state.raw_request, state.goal_target_version_hint)
            state.set_goal(goal)
            _emit(AgentEventType.GOAL_CREATED, f"목표 파싱 완료: {goal.goal}", state)
            return {"agent_state": state}

        def planner_node(g: GraphState) -> dict:
            state = g["agent_state"]
            state.increment_iteration()
            is_replan = bool(state.plan)
            new_tasks = self.planner.replan(state) if is_replan else self.planner.initial_plan(state)
            added = [t for t in new_tasks if state.add_task(t)]
            if is_replan and not added:
                state.planner_exhausted = True
            ev_type = AgentEventType.REPLANNING if is_replan else AgentEventType.PLANNING
            _emit(ev_type, f"Task {len(added)}건 추가", state, task_ids=[t.id for t in added])
            return {"agent_state": state}

        async def executor_node(g: GraphState) -> dict:
            state = g["agent_state"]
            batch = state.pop_pending_batch()

            def _tool_emit(ev_type: AgentEventType, payload: dict) -> None:
                _emit(ev_type, ev_type.value, state, **payload)

            results = await self.executor.execute_batch(batch, _ctx(state), _tool_emit)
            state.memory_working["_last_batch_results"] = results
            return {"agent_state": state}

        def observer_node(g: GraphState) -> dict:
            state = g["agent_state"]
            results = state.memory_working.pop("_last_batch_results", [])
            obs_list = self.observer.observe_batch(results, state)
            for obs in obs_list:
                _emit(AgentEventType.OBSERVATION_CREATED, obs.observation, state, observation_id=obs.id)
            return {"agent_state": state}

        def critic_node(g: GraphState) -> dict:
            state = g["agent_state"]
            _emit(AgentEventType.CRITIC_STARTED, "충분성 판단 중", state)
            verdict = self.critic.judge(state)
            state.memory_working["_last_verdict"] = verdict.model_dump()
            return {"agent_state": state}

        def route_after_critic(g: GraphState) -> str:
            state = g["agent_state"]
            verdict_dict = state.memory_working.get("_last_verdict", {})
            if state.is_guardrail_exceeded() or verdict_dict.get("sufficient") or state.planner_exhausted:
                return "finalizer"
            return "planner"

        def finalizer_node(g: GraphState) -> dict:
            state = g["agent_state"]
            verdict_dict = state.memory_working.get("_last_verdict", {})
            verdict = CriticVerdict.model_validate(verdict_dict) if verdict_dict else None
            sufficient = bool(verdict and verdict.sufficient)

            if state.is_guardrail_exceeded() and not sufficient:
                stopped_reason = "max_iterations" if state.iteration >= state.max_iterations else "max_tool_calls"
                status = AgentStatus.MAX_ITERATIONS_REACHED
            elif state.planner_exhausted and not sufficient:
                stopped_reason = "planner_exhausted"
                status = AgentStatus.COMPLETED
            else:
                stopped_reason = "critic_sufficient"
                status = AgentStatus.COMPLETED

            conclusion = FinalConclusion(
                summary=self._build_summary(state, verdict, stopped_reason),
                goal_met=sufficient,
                missing_evidence=verdict.missing_evidence if verdict else [],
                citations=state.evidence,
                stopped_reason=stopped_reason,
            )
            state.finalize(conclusion, status)
            _emit(AgentEventType.GOAL_COMPLETED, conclusion.summary, state)
            return {"agent_state": state}

        graph = StateGraph(GraphState)
        graph.add_node("goal_manager", goal_manager_node)
        graph.add_node("planner", planner_node)
        graph.add_node("executor", executor_node)
        graph.add_node("observer", observer_node)
        graph.add_node("critic", critic_node)
        graph.add_node("finalizer", finalizer_node)

        graph.add_edge(START, "goal_manager")
        graph.add_edge("goal_manager", "planner")
        graph.add_edge("planner", "executor")
        graph.add_edge("executor", "observer")
        graph.add_edge("observer", "critic")
        graph.add_conditional_edges("critic", route_after_critic, {"planner": "planner", "finalizer": "finalizer"})
        graph.add_edge("finalizer", END)

        return graph.compile()

    def _build_summary(self, state: AgentState, verdict: CriticVerdict | None, stopped_reason: str) -> str:
        goal_text = state.goal.goal if state.goal else "(unknown goal)"
        tool_names = ", ".join(dict.fromkeys(c.tool_name for c in state.tool_calls)) or "없음"
        lines = [
            f"목표: {goal_text}",
            f"수집 수단: {tool_names}",
            f"종료 사유: {stopped_reason}",
        ]
        if verdict and not verdict.sufficient:
            lines.append("미해결 사항: " + "; ".join(verdict.missing_evidence))
        fallback_summary = " / ".join(lines)

        if self._llm_client is not None and self._llm_client.is_configured:
            context = "\n".join(lines) + "\n\n주요 근거:\n" + "\n".join(
                f"- [{ev.source_type}] {ev.title}" for ev in state.evidence[:10]
            )
            generated = self._llm_client.summarize(
                "위 정보를 바탕으로 이번 자율 에이전트 실행 결과를 3~4문장으로 요약해줘.", context
            )
            if generated:
                return generated
        return fallback_summary


def build_agent_runtime(
    *,
    mcp_client: MCPClient,
    rag: RAGRetriever,
    llm_client: LLMClient | None,
    registry: ToolRegistry,
    settings: Settings,
) -> AgentRuntime:
    return AgentRuntime(mcp_client=mcp_client, rag=rag, llm_client=llm_client, registry=registry, settings=settings)
