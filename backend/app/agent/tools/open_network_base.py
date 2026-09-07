"""Open Network Tool 공용 베이스 (Section 6).

``LLMClient.is_configured`` 와 동일한 철학: API 키/설정이 없으면 예외를 던지지
않고 ``ToolResult(not_configured=True)`` 로 조용히 fallback한다 — 실행을 절대
깨뜨리지 않는다. 실제 호출은 도메인 allowlist를 통과한 URL에 대해서만 한다.
"""

from __future__ import annotations

import httpx

from app.agent.tools.base import AgentTool
from app.models.agent import ToolResult


class OpenNetworkTool(AgentTool):
    allowed_domains: tuple[str, ...] = ()

    def __init__(self, *, enabled: bool, timeout: float = 10.0) -> None:
        self._enabled = enabled
        self._timeout = timeout

    @property
    def is_configured(self) -> bool:
        return self._enabled

    def _not_configured_result(self) -> ToolResult:
        return ToolResult(
            tool_name=self.name,
            ok=False,
            not_configured=True,
            summary=f"{self.name}이(가) 설정되지 않아 이 근거는 수집하지 못했습니다.",
        )

    def _check_allowlist(self, url: str) -> None:
        host = httpx.URL(url).host or ""
        if self.allowed_domains and not any(host == d or host.endswith(f".{d}") for d in self.allowed_domains):
            raise PermissionError(f"허용되지 않은 도메인입니다: {host}")
