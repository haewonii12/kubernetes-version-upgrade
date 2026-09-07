"""LongTermMemory — 재사용 가치가 있는 장기 정보 (Section 7).

이번 pass에서는 스텁이다 — 단일 JSON 키/값 저장소로만 존재하고 Planner/Critic
판단 로직에는 아직 연결하지 않는다 (과도한 복잡성 회피). 인터페이스를 먼저
분리해 둬서, 나중에 벡터 스토어 등으로 교체해도 호출부가 바뀌지 않도록 한다
(``RAGRetriever`` 가 스스로 밝힌 것과 동일한 설계 철학).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class LongTermMemory:
    def __init__(self, memory_dir: Path) -> None:
        self._path = memory_dir / "longterm.json"

    def _load(self) -> dict[str, Any]:
        if not self._path.exists():
            return {}
        return json.loads(self._path.read_text(encoding="utf-8"))

    def remember(self, key: str, value: Any) -> None:
        data = self._load()
        data[key] = value
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def recall(self, key: str) -> Any | None:
        return self._load().get(key)
