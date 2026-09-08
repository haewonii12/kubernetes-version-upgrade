"""GoalManager — 자연어 요청을 구조화된 Goal로 변환한다 (Section 3).

규칙 기반 파싱을 기본으로 하고, LLM이 설정된 경우에만 보강을 시도한다 (LLM 실패/
미설정 시 규칙 기반 결과로 조용히 fallback — agents/planner.py의
``_summarize_release_notes`` 와 동일한 안전한 fallback 계약).
"""

from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime

from app.llm.client import LLMClient
from app.models.agent import Goal

logger = logging.getLogger(__name__)

_UPGRADE_KEYWORDS = ("업그레이드", "upgrade", "이관", "migration")

# "1.32 클러스터를 1.37로 업그레이드" 처럼 목표 버전 바로 뒤에 "로/으로"+업그레이드 표현이
# 붙는 한국어/영어 패턴을 우선 시도하고, 못 찾으면 "to 1.37" 류를, 그래도 없으면 문장에서
# 마지막으로 언급된 버전 번호를 목표 버전으로 추정한다 (예: "1.32 -> 1.37"에서 1.37).
_VERSION_TOKEN = r"v?(\d+\.\d+(?:\.\d+)?)"
_TARGET_VERSION_PATTERNS = [
    re.compile(_VERSION_TOKEN + r"\s*(?:로|으로)\s*(?:업그레이드|이관|migration|upgrade)", re.IGNORECASE),
    re.compile(r"(?:to|→|->)\s*" + _VERSION_TOKEN, re.IGNORECASE),
]
_ANY_VERSION = re.compile(r"\b\d+\.\d+(?:\.\d+)?\b")


def _extract_target_version_from_text(text: str) -> str | None:
    for pattern in _TARGET_VERSION_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(1)
    all_versions = _ANY_VERSION.findall(text)
    # 버전이 두 개 이상 언급됐다면(현재 버전 + 목표 버전) 마지막 것을 목표로 본다.
    # 하나만 언급됐다면 그건 보통 "현재 버전"을 설명하는 것이라 목표로 추정하지 않는다.
    return all_versions[-1] if len(all_versions) >= 2 else None

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
        # UI의 Target Version 드롭다운은 RAG에 이미 문서가 있는 버전만 보여준다
        # (rag.list_target_kubernetes_versions). 아직 RAG에 없는 버전(예: 최신 릴리스)을
        # 목표로 요청하면 드롭다운에는 없으므로, 사용자가 문장에 직접 쓴 버전을 놓치지 않도록
        # 텍스트에서도 추출을 시도한다 — 명시적으로 넘어온 target_version이 우선한다.
        resolved_target_version = target_version or _extract_target_version_from_text(request)

        text = request.lower()
        is_upgrade_goal = resolved_target_version is not None or any(k in text for k in _UPGRADE_KEYWORDS)

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
            target_version=resolved_target_version,
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
                target_version=data.get("target_version") or fallback.target_version,
                success_criteria=data.get("success_criteria") or fallback.success_criteria,
                created_at=datetime.now(UTC),
            )
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            logger.warning("GoalManager LLM 응답 파싱 실패, 규칙 기반 Goal로 fallback: %s", exc)
            return None
