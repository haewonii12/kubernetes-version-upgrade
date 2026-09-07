"""EpisodicMemory — 과거 실행(run) 기록 (Section 7).

``analysis_service.py`` 의 ``_save_snapshot``/``load_snapshot``/``list_snapshots`` 와
동일한 패턴 — run 하나당 JSON 파일 하나, ``settings.agent_memory_dir/episodes/`` 아래.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.models.agent import AgentReport


class EpisodicMemory:
    def __init__(self, memory_dir: Path) -> None:
        self._episodes_dir = memory_dir / "episodes"

    def save_run(self, report: AgentReport) -> None:
        self._episodes_dir.mkdir(parents=True, exist_ok=True)
        path = self._episodes_dir / f"{report.run_id}.json"
        path.write_text(report.model_dump_json(indent=2), encoding="utf-8")

    def load_run(self, run_id: str) -> AgentReport | None:
        path = self._episodes_dir / f"{run_id}.json"
        if not path.exists():
            return None
        return AgentReport.model_validate(json.loads(path.read_text(encoding="utf-8")))

    def list_recent(self, limit: int = 20) -> list[dict]:
        if not self._episodes_dir.exists():
            return []
        result = []
        for path in sorted(self._episodes_dir.glob("*.json"), reverse=True)[:limit]:
            data = json.loads(path.read_text(encoding="utf-8"))
            result.append(
                {
                    "run_id": data["run_id"],
                    "created_at": data["created_at"],
                    "goal": data["goal"]["goal"],
                    "goal_met": data["final_conclusion"]["goal_met"],
                }
            )
        return result
