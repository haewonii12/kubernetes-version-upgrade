"""InternalRagTool — RAGRetriever.search() 를 감싼 AgentTool (Section 5/7 Knowledge)."""

from __future__ import annotations

from app.agent.tools.base import AgentTool, ToolContext
from app.models.agent import Evidence, Task, ToolCapability, ToolResult


class InternalRagTool(AgentTool):
    name = "internal_rag_search"
    description = (
        "버전 skew 정책, kubeadm 업그레이드 절차 등 사내 RAG 문서(rag/documents/)에서 "
        "자유 텍스트로 근거를 검색한다."
    )
    capabilities = [ToolCapability.KNOWLEDGE_SEARCH]

    async def execute(self, task: Task, ctx: ToolContext) -> ToolResult:
        assert ctx.rag is not None
        query = task.input.get("query") or task.description
        top_k = task.input.get("top_k", 5)
        refs = ctx.rag.search(query, top_k=top_k)
        evidence = [Evidence.from_rag_reference(ref) for ref in refs]
        return ToolResult(
            tool_name=self.name,
            ok=True,
            data={"references": [r.model_dump(mode="json") for r in refs]},
            summary=f"RAG 검색 결과 {len(refs)}건 ('{query}')",
            evidence=evidence,
        )
