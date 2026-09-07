"""AgentTool 추상화 (Section 5).

Executor는 이 인터페이스만 알면 되고, 실제 Kubernetes/RAG/Web 도메인 로직은 각
구체 Tool 구현체 안에 있다 — Executor 자체에는 도메인 로직을 하드코딩하지 않는다.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import ClassVar, TYPE_CHECKING

from app.core.config import Settings
from app.llm.client import LLMClient
from app.mcp.client import MCPClient
from app.models.agent import Task, ToolCapability, ToolResult
from app.rag.retriever import RAGRetriever

if TYPE_CHECKING:
    from app.agent.state import AgentState


@dataclass
class ToolContext:
    """Tool 실행에 필요한 의존성 묶음. Tool은 이 중 필요한 것만 골라 쓴다."""

    state: "AgentState"
    mcp_client: MCPClient | None
    rag: RAGRetriever | None
    llm_client: LLMClient | None
    settings: Settings


class AgentTool(abc.ABC):
    name: ClassVar[str]
    description: ClassVar[str]
    capabilities: ClassVar[list[ToolCapability]]
    is_mutating: ClassVar[bool] = False

    @abc.abstractmethod
    async def execute(self, task: Task, ctx: ToolContext) -> ToolResult: ...

    def describe_for_retrieval(self) -> str:
        return f"{self.name}: {self.description}"
