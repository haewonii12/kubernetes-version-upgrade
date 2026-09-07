"""WebSearchTool — 실제 Web Search API 호출 + API 키 없으면 graceful fallback."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

import httpx

from app.agent.tools.base import ToolContext
from app.agent.tools.open_network_base import OpenNetworkTool
from app.models.agent import Evidence, Task, ToolCapability, ToolResult

logger = logging.getLogger(__name__)


class WebSearchTool(OpenNetworkTool):
    name = "web_search"
    description = "인터넷 검색으로 특정 컴포넌트의 최신 버전/호환성 이슈 등 최신 정보를 찾는다."
    capabilities = [ToolCapability.WEB_SEARCH]

    def __init__(self, *, api_key: str | None, endpoint: str, timeout: float = 10.0) -> None:
        super().__init__(enabled=bool(api_key), timeout=timeout)
        self._api_key = api_key
        self._endpoint = endpoint

    async def execute(self, task: Task, ctx: ToolContext) -> ToolResult:
        if not self.is_configured:
            return self._not_configured_result()
        query = task.input.get("query") or task.description
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(
                    self._endpoint,
                    params={"q": query},
                    headers={"X-Subscription-Token": self._api_key or ""},
                )
            resp.raise_for_status()
            results = resp.json().get("web", {}).get("results", [])[:5]
        except Exception as exc:  # noqa: BLE001 — 네트워크 실패는 크래시가 아니라 실패 결과로
            logger.warning("web_search 호출 실패: %s", exc, exc_info=True)
            return ToolResult(tool_name=self.name, ok=False, summary=f"웹 검색 실패: {exc}", error=str(exc))

        evidence = [
            Evidence(
                source_type="web_search",
                title=r.get("title", ""),
                url=r.get("url"),
                excerpt=r.get("description"),
                retrieved_at=datetime.now(UTC),
            )
            for r in results
        ]
        return ToolResult(tool_name=self.name, ok=True, summary=f"웹 검색 결과 {len(evidence)}건 ('{query}')", evidence=evidence)
