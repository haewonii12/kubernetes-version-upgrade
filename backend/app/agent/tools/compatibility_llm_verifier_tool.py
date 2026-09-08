"""CompatibilityLlmVerifierTool — RAG 판정 + Web/GitHub 근거를 LLM으로 종합한다.

기존에는 web_search/github_search 결과가 그냥 Evidence(인용)로만 붙고 실제
Compatibility 판정(COMPATIBLE/WARNING/...)에는 영향을 주지 않았다. 이 Tool은
그 근거를 실제 판정으로 승격시킨다:

  - RAG가 이미 판정한 버전도 웹/GitHub 근거로 다시 확인하고, 근거가 다르면
    그 근거를 우선해 덮어쓴다 (이유를 reason에 남긴다).
  - RAG에 문서가 아예 없는 버전(예: 갓 나온 목표 버전)은 이 결과로 채워 넣는다.

LLM이 설정되지 않았으면 아예 실행되지 않는다 — RAG 판정 자체는 항상 100%
결정론적으로 유지되고, 이 재검증은 그 위에 얹는 선택적 보강일 뿐이다.
"""

from __future__ import annotations

import json
import logging

from app.agent.tools.base import AgentTool, ToolContext
from app.models.agent import Task, ToolCapability, ToolResult
from app.models.compatibility import CompatibilityResult, CompatibilityStatus

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "당신은 Kubernetes 컴포넌트 호환성을 판정하는 보조 도구입니다. "
    "주어진 '기존 판정'(RAG 문서 기반)과 '웹 검색/GitHub 근거'만 사용해서 "
    "각 목표 버전에 대한 최종 판정을 내리세요. 웹 근거가 기존 판정과 다르면 "
    "웹 근거를 우선하되 그 사실과 이유를 reason에 명시하세요. 근거가 불충분하면 "
    "추측하지 말고 UNKNOWN으로 답하세요. "
    "반드시 아래 JSON 스키마로만 답하세요 (다른 텍스트 금지):\n"
    '{"judgments": [{"target_kubernetes_version": "1.37", '
    '"status": "COMPATIBLE" | "INCOMPATIBLE" | "WARNING" | "UNKNOWN", "reason": "..."}]}'
)


class CompatibilityLlmVerifierTool(AgentTool):
    name = "compatibility_llm_verifier"
    description = "RAG 판정과 웹/GitHub 근거를 LLM으로 종합해 Compatibility를 재검증하거나 RAG에 없는 버전을 채운다."
    capabilities = [ToolCapability.COMPATIBILITY]

    async def execute(self, task: Task, ctx: ToolContext) -> ToolResult:
        if ctx.llm_client is None or not ctx.llm_client.is_configured:
            return ToolResult(tool_name=self.name, ok=False, not_configured=True, summary="LLM이 설정되지 않아 재검증을 건너뜁니다.")

        component = task.input.get("component")
        current_version = task.input.get("current_version")
        rag_judgments = task.input.get("rag_judgments", [])
        evidence = task.input.get("evidence", [])
        if not component or not evidence:
            return ToolResult(tool_name=self.name, ok=False, summary="재검증에 필요한 근거가 없습니다.", error="missing_input")

        target_versions = sorted({j["target_kubernetes_version"] for j in rag_judgments if j.get("target_kubernetes_version")})
        rag_text = "\n".join(f"- {j['target_kubernetes_version']}: {j['status']} ({j.get('reason') or ''})" for j in rag_judgments) or "(RAG 판정 없음 — 문서가 없는 버전)"
        evidence_text = "\n".join(f"- [{e.get('source_type')}] {e.get('title')}: {(e.get('excerpt') or '')[:300]}" for e in evidence)

        user_prompt = (
            f"컴포넌트: {component} (현재 버전: {current_version})\n"
            f"판정 대상 버전: {', '.join(target_versions) or '(RAG 판정에 없음)'}\n\n"
            f"[기존 RAG 판정]\n{rag_text}\n\n"
            f"[웹 검색/GitHub 근거]\n{evidence_text}"
        )

        raw = ctx.llm_client.complete(
            [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ]
        )
        if raw is None:
            return ToolResult(tool_name=self.name, ok=False, summary="LLM 호출이 실패했습니다.", error="llm_call_failed")

        try:
            judgments = json.loads(raw)["judgments"]
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            logger.warning("compatibility_llm_verifier 응답 파싱 실패: %s", exc)
            return ToolResult(tool_name=self.name, ok=False, summary="LLM 응답을 해석할 수 없습니다.", error="parse_failed")

        results = ctx.state.memory_working.setdefault("compatibility_results", [])
        updated = 0
        for j in judgments:
            target_minor = j.get("target_kubernetes_version")
            status = j.get("status")
            if not target_minor or status not in CompatibilityStatus.__members__:
                continue
            new_result = CompatibilityResult(
                component=component,
                current_version=current_version,
                target_kubernetes_version=target_minor,
                status=CompatibilityStatus(status),
                reason=j.get("reason") or "",
                verified_by="llm_web_search",
            )
            for i, existing in enumerate(results):
                if existing["component"] == component and existing["target_kubernetes_version"] == target_minor:
                    results[i] = new_result.model_dump(mode="json")
                    break
            else:
                results.append(new_result.model_dump(mode="json"))
            updated += 1

        return ToolResult(
            tool_name=self.name,
            ok=True,
            data={"judgments": judgments},
            summary=f"{component}: 웹/GitHub 근거 기반 재검증 {updated}건 완료",
        )
