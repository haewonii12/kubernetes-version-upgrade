"""GitHubTool — GitHub REST API 조회 (익명 호출 가능, 토큰 있으면 rate limit 완화)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

import httpx

from app.agent.tools.base import ToolContext
from app.agent.tools.open_network_base import OpenNetworkTool
from app.models.agent import Evidence, Task, ToolCapability, ToolResult

logger = logging.getLogger(__name__)


class GitHubTool(OpenNetworkTool):
    name = "github_search"
    description = "kubernetes/kubernetes 등 GitHub 저장소의 Release/Issue를 검색해 컴포넌트 이슈/변경 이력을 찾는다."
    capabilities = [ToolCapability.SOURCE_CODE]
    allowed_domains = ("api.github.com", "github.com")

    def __init__(self, *, enabled: bool, token: str | None = None, timeout: float = 10.0) -> None:
        super().__init__(enabled=enabled, timeout=timeout)
        self._token = token

    async def execute(self, task: Task, ctx: ToolContext) -> ToolResult:
        if not self.is_configured:
            return self._not_configured_result()
        query = task.input.get("query") or task.description
        repo = task.input.get("repo")
        search_query = f"{query} repo:{repo}" if repo else query
        headers = {"Accept": "application/vnd.github+json"}
        if self._token:
            headers["Authorization"] = f"token {self._token}"
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(
                    "https://api.github.com/search/issues",
                    params={"q": search_query, "per_page": 5},
                    headers=headers,
                )
            resp.raise_for_status()
            items = resp.json().get("items", [])
        except Exception as exc:  # noqa: BLE001
            logger.warning("github_search 호출 실패: %s", exc, exc_info=True)
            return ToolResult(tool_name=self.name, ok=False, summary=f"GitHub 검색 실패: {exc}", error=str(exc))

        evidence = [
            Evidence(
                source_type="github",
                title=item.get("title", ""),
                url=item.get("html_url"),
                excerpt=(item.get("body") or "")[:300],
                retrieved_at=datetime.now(UTC),
            )
            for item in items
        ]
        return ToolResult(tool_name=self.name, ok=True, summary=f"GitHub 검색 결과 {len(evidence)}건 ('{search_query}')", evidence=evidence)
