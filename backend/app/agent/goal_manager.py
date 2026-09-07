"""GoalManager — 자연어 요청을 구조화된 Goal로 변환한다 (Section 3).

규칙 기반 파싱을 기본으로 하고, LLM이 설정된 경우에만 보강을 시도한다 (LLM 실패/
미설정 시 규칙 기반 결과로 조용히 fallback — agents/planner.py의
``_summarize_release_notes`` 와 동일한 안전한 fallback 계약).
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime

from app.llm.client import LLMClient
from app.models.agent import Goal

logger = logging.getLogger(__name__)

_UPGRADE_KEYWORDS = ("업그레이드", "upgrade", "이관", "migration")

_GOAL_EXTRACTION_SYSTEM_PROMPT = (
    "당신은 Kubernetes 운영자의 자연어 요청을 구조화된 목표로 변환하는 보조 도구입니다. "
    "반드시 아래 JSON 스키마로만 답하세요 (다른 텍스트 금지):\n"
    '{"goal": "<한 문장 목표>", "target_version": "<x.y 형식 또는 null>", '
    '"success_criteria": ["<검증 가능한 완료 조건>", ...]}\n'
    "success_criteria는 사용자가 명시적으로 요청한 범위를 벗어나지 않아야 합니다 — "
    "단순 현황 파악 요청에 업그레이드 실행 계획 같은 조건을 추가하지 마세요."
)


class GoalManager:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self._llm = llm_client

    def parse_goal(self, request: str, target_version: str | None) -> Goal:
        rule_based = self._rule_based_parse(request, target_version)
        if self._llm is not None and self._llm.is_configured:
            enriched = self._llm_parse(request, target_version, rule_based)
            if enriched is not None:
                return enriched
        return rule_based

    def _rule_based_parse(self, request: str, target_version: str | None) -> Goal:
        text = request.lower()
        is_upgrade_goal = target_version is not None or any(k in text for k in _UPGRADE_KEYWORDS)

        if is_upgrade_goal:
            criteria = [
                "현재 클러스터 상태를 사실 기반으로 파악한다",
                "설치된 컴포넌트의 목표 버전 호환성을 판정한다",
                "목표 버전까지 Deprecated/Removed API 영향을 확인한다",
                "종합 Risk 및 준비 복잡도를 산정한다",
            ]
        else:
            criteria = ["클러스터의 현재 버전/노드/설정 상태를 사실 기반으로 파악한다"]

        return Goal(
            goal=request,
            target_version=target_version,
            success_criteria=criteria,
            created_at=datetime.now(UTC),
        )

    def _llm_parse(self, request: str, target_version: str | None, fallback: Goal) -> Goal | None:
        assert self._llm is not None
        user_prompt = f"요청: {request}\n" + (f"목표 버전 힌트: {target_version}" if target_version else "목표 버전 힌트: 없음")
        raw = self._llm.complete(
            [
                {"role": "system", "content": _GOAL_EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ]
        )
        if raw is None:
            return None
        try:
            data = json.loads(raw)
            return Goal(
                goal=data.get("goal") or fallback.goal,
                target_version=data.get("target_version") or target_version,
                success_criteria=data.get("success_criteria") or fallback.success_criteria,
                created_at=datetime.now(UTC),
            )
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            logger.warning("GoalManager LLM 응답 파싱 실패, 규칙 기반 Goal로 fallback: %s", exc)
            return None
