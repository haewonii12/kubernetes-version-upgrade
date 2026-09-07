"""OfficialKubernetesDocsTool — kubernetes.io 공식 문서 조회 (도메인 allowlist 적용)."""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime

import httpx

from app.agent.tools.base import ToolContext
from app.agent.tools.open_network_base import OpenNetworkTool
from app.models.agent import Evidence, Task, ToolCapability, ToolResult

logger = logging.getLogger(__name__)

_TAG_RE = re.compile(r"<[^>]+>")


def _strip_tags(html: str, limit: int = 2000) -> str:
    text = _TAG_RE.sub(" ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


class OfficialKubernetesDocsTool(OpenNetworkTool):
    name = "official_kubernetes_docs"
    description = "kubernetes.io 공식 문서(릴리스 노트, 버전 skew 정책, deprecated API 가이드 등)를 조회한다."
    capabilities = [ToolCapability.OFFICIAL_DOCS]
    allowed_domains = ("kubernetes.io",)

    def __init__(self, *, enabled: bool, timeout: float = 10.0) -> None:
        super().__init__(enabled=enabled, timeout=timeout)

    async def execute(self, task: Task, ctx: ToolContext) -> ToolResult:
        if not self.is_configured:
            return self._not_configured_result()
        url = task.input.get("url")
        if not url:
            return ToolResult(tool_name=self.name, ok=False, summary="조회할 문서 URL이 지정되지 않았습니다.", error="missing_url")
        try:
            self._check_allowlist(url)
            async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
                resp = await client.get(url)
            resp.raise_for_status()
            excerpt = _strip_tags(resp.text)
        except Exception as exc:  # noqa: BLE001
            logger.warning("official_kubernetes_docs 조회 실패: %s", exc, exc_info=True)
            return ToolResult(tool_name=self.name, ok=False, summary=f"공식 문서 조회 실패: {exc}", error=str(exc))

        evidence = [Evidence(source_type="official_docs", title=url, url=url, excerpt=excerpt, retrieved_at=datetime.now(UTC))]
        return ToolResult(tool_name=self.name, ok=True, summary=f"공식 문서 조회 완료: {url}", evidence=evidence)
