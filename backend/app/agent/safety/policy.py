"""PolicyGuard — Read-Only 강제 (Section 8).

이번 pass는 "분석과 계획 생성까지"만 구현한다 — mutating Tool은 아직 하나도
등록되어 있지 않다 (``tools/registry_builder.py`` 참고). 이 모듈은 향후 mutating
Tool을 작성하는 사람이 명령 문자열을 만들기 전에 검증할 수 있도록 미리 준비해
두는 정책 가드다. ``Executor`` 는 ``AgentTool.is_mutating`` 플래그만으로 이미
mutating Tool 실행을 차단하므로, 지금 당장 이 가드를 호출하는 곳은 없다.
"""

from __future__ import annotations

MUTATING_VERBS: frozenset[str] = frozenset(
    {"delete", "patch", "apply", "create", "scale", "rollout", "cordon", "drain", "upgrade", "exec"}
)

READ_ONLY_VERBS: frozenset[str] = frozenset({"get", "list", "watch", "logs", "describe"})


class PolicyViolation(Exception):
    pass


class PolicyGuard:
    @staticmethod
    def assert_read_only(verb: str) -> None:
        if verb.lower() in MUTATING_VERBS:
            raise PolicyViolation(f"'{verb}'는 mutating 작업이라 자율 실행이 허용되지 않습니다 (Section 8).")
