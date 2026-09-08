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

import re
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

            structured = self._build_structured_conclusion(state)
            conclusion = FinalConclusion(
                summary=self._build_summary(state, verdict, stopped_reason, structured),
                goal_met=sufficient,
                missing_evidence=verdict.missing_evidence if verdict else [],
                citations=state.evidence,
                stopped_reason=stopped_reason,
                readiness=structured["readiness"],
                risks=structured["risks"],
                unresolved_components=structured["unresolved_components"],
                deprecated_action_required_count=structured["deprecated_action_required_count"],
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

    def _build_structured_conclusion(self, state: AgentState) -> dict:
        """risk_analyzer/compatibility_checker/deprecated_api_checker가 이미 계산해 둔
        결과를 FinalConclusion의 구조화된 필드로 뽑아낸다 — 프론트가 이 문자열을
        파싱하지 않고 카드/뱃지로 바로 렌더링할 수 있도록 하기 위함이다 (예전에는
        이 데이터가 summary 문자열 하나로만 뭉쳐 나가서 UI가 통짜 텍스트만 보여줬다).
        """
        severity_order = {"BLOCKER": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
        risks = state.memory_working.get("risks", [])
        # 같은 근본 원인이 upgrade_path의 여러 target minor마다 한 번씩 반복 등장할 수
        # 있다 (예: fleet-agent INCOMPATIBLE이 1.33/1.34/1.35/1.36 각각에 대해 하나씩).
        # finding 문구에서 "Kubernetes 1.33 기준" 같은 버전 부분만 정규화해 dedup한다.
        deduped: dict[tuple[str, str], dict] = {}
        for r in risks:
            normalized = re.sub(r"Kubernetes\s+\d+\.\d+(\.\d+)?\s*기준", "Kubernetes X.Y 기준", r["finding"])
            deduped.setdefault((r["severity"], normalized), r)
        # UI에는 전체를 보여준다 — 개수 제한은 LLM 프롬프트 컨텍스트를 만들 때만 따로 건다.
        all_risks = sorted(deduped.values(), key=lambda r: severity_order.get(r["severity"], 9))

        unresolved_components = self._unresolved_compatibility_components(state)

        deprecated_findings = state.memory_working.get("deprecated_findings", [])
        deprecated_action_required_count = sum(1 for f in deprecated_findings if f["status"] != "OK")

        return {
            "readiness": state.memory_working.get("readiness"),
            "risks": all_risks,
            "unresolved_components": unresolved_components,
            "deprecated_action_required_count": deprecated_action_required_count,
        }

    def _build_summary(
        self, state: AgentState, verdict: CriticVerdict | None, stopped_reason: str, structured: dict
    ) -> str:
        """서술형 결론. 규칙 기반 fallback은 짧게, LLM이 설정되면 구조화된 데이터를
        근거로 실제 권고(지금 진행해도 되는지/핵심 위험/사전 확인 사항)를 생성한다.
        """
        goal_text = state.goal.goal if state.goal else "(unknown goal)"
        readiness = structured["readiness"]
        fallback_parts = [f"목표: {goal_text}", f"종료 사유: {stopped_reason}"]
        if readiness:
            fallback_parts.append(f"업그레이드 준비 복잡도 {readiness['complexity']}%")
        if not (verdict and verdict.sufficient):
            fallback_parts.append("아래 상세 결과(Risk/미해결 컴포넌트/근거 출처)를 확인하세요")
        fallback_summary = " — ".join(fallback_parts)

        if self._llm_client is not None and self._llm_client.is_configured:
            context_lines = [f"목표: {goal_text}"]
            if readiness:
                context_lines.append(
                    f"업그레이드 준비 복잡도: {readiness['complexity']}% "
                    f"(BLOCKER {readiness['blocker_count']}, HIGH {readiness['high_count']}, "
                    f"MEDIUM {readiness['medium_count']}, LOW {readiness['low_count']})"
                )
            # LLM 프롬프트는 토큰 비용/집중도를 위해 상위 5건만 넣는다 — UI는
            # FinalConclusion.risks 전체를 그대로 보여준다 (개수 제한 없음).
            top_risks_for_prompt = structured["risks"][:5]
            if top_risks_for_prompt:
                context_lines.append("주요 Risk:")
                context_lines.extend(f"- [{r['severity']}] {r['finding']} — {r['recommendation']}" for r in top_risks_for_prompt)
            if structured["unresolved_components"]:
                context_lines.append("수동 확인 필요 컴포넌트: " + ", ".join(structured["unresolved_components"][:15]))
            if structured["deprecated_action_required_count"]:
                context_lines.append(f"Deprecated/Removed API 조치 필요: {structured['deprecated_action_required_count']}건")
            if verdict and not verdict.sufficient:
                context_lines.append("Critic 판단(불충분 사유): " + "; ".join(verdict.missing_evidence))
            external_evidence = "\n".join(f"- [{ev.source_type}] {ev.title}" for ev in state.evidence if ev.source_type != "rag")
            context = "\n".join(context_lines) + "\n\n외부 조사로 확보한 근거 (RAG 제외):\n" + external_evidence[:3000]

            generated = self._llm_client.summarize(
                "당신은 Kubernetes 업그레이드 위험도를 평가하는 전문가입니다. 위 데이터를 종합해 "
                "이번 업그레이드를 지금 진행해도 되는지, 가장 중요한 위험 요인은 무엇인지, 진행 전에 "
                "반드시 수동으로 확인해야 할 항목은 무엇인지 4~6문장으로 명확하게 설명하세요. "
                "위 데이터에 없는 내용은 추측하지 마세요.",
                context,
            )
            if generated:
                return generated
        return fallback_summary

    def _unresolved_compatibility_components(self, state: AgentState) -> list[str]:
        severity_order = {"INCOMPATIBLE": 0, "WARNING": 1, "UNKNOWN": 2, "COMPATIBLE": 3}
        by_component: dict[str, str] = {}
        for r in state.memory_working.get("compatibility_results", []):
            current = by_component.get(r["component"])
            if current is None or severity_order.get(r["status"], 9) < severity_order.get(current, 9):
                by_component[r["component"]] = r["status"]
        return sorted(name for name, status in by_component.items() if status != "COMPATIBLE")


def build_agent_runtime(
    *,
    mcp_client: MCPClient,
    rag: RAGRetriever,
    llm_client: LLMClient | None,
    registry: ToolRegistry,
    settings: Settings,
) -> AgentRuntime:
    return AgentRuntime(mcp_client=mcp_client, rag=rag, llm_client=llm_client, registry=registry, settings=settings)
