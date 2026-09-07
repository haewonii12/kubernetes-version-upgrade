"""공유 fixture: MockMCPClient(기존), 실제 RAGRetriever(오프라인), FakeLLMClient(신규 테스트 더블).

이 저장소에는 이전까지 테스트가 전혀 없었다 — 이 파일이 agi 브랜치의 첫 pytest
컨벤션이다. 모든 fixture는 완전히 오프라인/결정론적이다: 실제 클러스터/LLM/
인터넷 연결이 전혀 필요 없다.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.core.config import settings
from app.mcp.client import MockMCPClient
from app.rag.retriever import RAGRetriever

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MOCK_FIXTURE_DIR = PROJECT_ROOT / "examples" / "mock-cluster"


class FakeLLMClient:
    """LLMClient와 동일한 인터페이스(duck-typing)를 갖는 테스트 더블.

    기본값은 ``is_configured=False`` — 대부분의 테스트가 규칙 기반 fallback
    경로만 타도록 하기 위함이다 (LLM 서버 없이도 결정론적으로 통과해야 한다).
    """

    def __init__(self, *, configured: bool = False, canned_response: str | None = None) -> None:
        self._configured = configured
        self._canned_response = canned_response

    @property
    def is_configured(self) -> bool:
        return self._configured

    def complete(self, messages: list[dict[str, str]], *, temperature: float = 0.2) -> str | None:
        if not self._configured:
            return None
        return self._canned_response

    def summarize(self, question: str, context: str) -> str | None:
        return self.complete([])


@pytest.fixture
def mock_mcp_client() -> MockMCPClient:
    return MockMCPClient(MOCK_FIXTURE_DIR)


@pytest.fixture(scope="session")
def rag_retriever() -> RAGRetriever:
    return RAGRetriever(settings.rag_documents_dir)


@pytest.fixture
def fake_llm_client() -> FakeLLMClient:
    return FakeLLMClient(configured=False)
