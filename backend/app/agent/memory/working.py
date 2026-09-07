"""WorkingMemory — 현재 실행(run) 동안의 스크래치 공간 (Section 7).

RAG(Knowledge)와 Agent Memory를 코드 레벨에서 분리해 두기 위한 얇은 wrapper다.
지금은 ``AgentState.memory_working`` (dict) 하나를 감싸는 것뿐이지만, 클래스로
분리해 두면 이 dict를 직접 여기저기서 주고받지 않고 "지금까지 이 run에서
무엇을 알아냈는가"라는 하나의 개념으로 다룰 수 있다.
"""

from __future__ import annotations

from typing import Any

from app.agent.state import AgentState


class WorkingMemory:
    def __init__(self, state: AgentState) -> None:
        self._state = state

    def get(self, key: str, default: Any = None) -> Any:
        return self._state.memory_working.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._state.memory_working[key] = value

    def has(self, key: str) -> bool:
        return key in self._state.memory_working
