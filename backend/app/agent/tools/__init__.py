"""ToolRegistry / ToolRetriever (Section 5).

ToolRetriever는 ``app.rag.retriever.RAGRetriever.search`` 와 동일한 TF-IDF 방식을
그대로 재사용한다 — 모든 Tool 설명을 한 번에 LLM context에 넣지 않고, Goal/Task와
관련성이 높은 것만 골라 넘기기 위함이다.
"""

from __future__ import annotations

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.agent.tools.base import AgentTool
from app.models.agent import ToolCapability


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, AgentTool] = {}

    def register(self, tool: AgentTool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> AgentTool:
        return self._tools[name]

    def has(self, name: str) -> bool:
        return name in self._tools

    def all(self) -> list[AgentTool]:
        return list(self._tools.values())


class ToolRetriever:
    """Goal/Task 텍스트와 Tool 설명 간 TF-IDF 코사인 유사도로 관련 Tool만 골라낸다."""

    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry
        tools = registry.all()
        self._names = [t.name for t in tools]
        texts = [t.describe_for_retrieval() for t in tools]
        self._vectorizer: TfidfVectorizer | None = TfidfVectorizer() if texts else None
        self._matrix = self._vectorizer.fit_transform(texts) if texts else None

    def retrieve(
        self,
        query: str,
        *,
        top_k: int = 3,
        required_capabilities: list[ToolCapability] | None = None,
    ) -> list[AgentTool]:
        candidates = self._registry.all()
        if required_capabilities:
            required = set(required_capabilities)
            candidates = [t for t in candidates if required & set(t.capabilities)]
        if not candidates or self._vectorizer is None or self._matrix is None:
            return candidates[:top_k]

        idx_map = [self._names.index(t.name) for t in candidates]
        q_vec = self._vectorizer.transform([query])
        sims = cosine_similarity(q_vec, self._matrix[idx_map])[0]
        ranked = sorted(zip(candidates, sims), key=lambda pair: pair[1], reverse=True)
        return [tool for tool, _score in ranked[:top_k]]
