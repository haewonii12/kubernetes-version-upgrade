"""RAG "검색" 결과를 "생성"으로 이어주는 선택적(optional) LLM 클라이언트.

사용자가 Web UI에서 LLM Endpoint/Model을 직접 입력한 경우에만 생성된다
(Section 24/25). OpenAI 호환 ``/v1/chat/completions`` 스펙을 쓰는 서버라면
어디든(로컬 Ollama, vLLM, LM Studio 등) 붙을 수 있다.

**중요**: 이 클라이언트는 Compatibility/Risk/Deprecated API 판정에는 전혀
관여하지 않는다 — 그 판정은 지금처럼 100% ``rag/documents/*.md``의 구조화된
룰 기반이다. 이 클라이언트는 오직 "이미 검증된 근거를 자연어로 요약"하는
용도로만 쓰이며, 실패해도 절대 분석 전체를 실패시키지 않는다 (모든 예외를
삼키고 ``None``을 반환 — 호출부는 항상 원문 발췌 등으로 fallback한다).
"""

from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_SECONDS = 30.0

SUMMARY_SYSTEM_PROMPT = (
    "당신은 Kubernetes 업그레이드 보고서를 작성하는 보조 도구입니다. "
    "반드시 사용자가 제공한 컨텍스트(근거 자료)에 있는 내용만 사용해 답하세요. "
    "컨텍스트에 없는 사실을 추측하거나 지어내지 마세요. "
    "한국어로, 불필요한 수식어 없이 간결하게 답하세요."
)


def _normalize_chat_completions_url(endpoint: str) -> str | None:
    endpoint = endpoint.strip().rstrip("/")
    if not endpoint or not (endpoint.startswith("http://") or endpoint.startswith("https://")):
        return None
    if endpoint.endswith("/chat/completions"):
        return endpoint
    if endpoint.endswith("/v1"):
        return f"{endpoint}/chat/completions"
    return f"{endpoint}/v1/chat/completions"


class LLMClient:
    def __init__(self, endpoint: str, model: str, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> None:
        self._url = _normalize_chat_completions_url(endpoint)
        self._model = model.strip()
        self._timeout = timeout

    @property
    def is_configured(self) -> bool:
        return bool(self._url and self._model)

    def summarize(self, question: str, context: str) -> str | None:
        """주어진 근거(context)를 바탕으로 question에 답하는 텍스트를 생성한다.

        실패(연결 불가, timeout, 잘못된 응답 등) 시 예외를 던지지 않고 ``None``을
        반환한다 — 호출부가 항상 안전하게 fallback할 수 있도록 하기 위함이다.
        """
        if not self.is_configured:
            return None
        try:
            response = httpx.post(
                self._url,
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                        {"role": "user", "content": f"[컨텍스트]\n{context}\n\n[요청]\n{question}"},
                    ],
                    "stream": False,
                    "temperature": 0.2,
                },
                timeout=self._timeout,
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return content.strip() or None
        except Exception:  # noqa: BLE001
            logger.warning("LLM 요약 생성 실패 (endpoint=%s, model=%s) — fallback 사용", self._url, self._model, exc_info=True)
            return None
