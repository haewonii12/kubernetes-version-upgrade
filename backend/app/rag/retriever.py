"""RAG 검색 (TF-IDF, 완전 로컬/오프라인 — Section 34 폐쇄망 요구사항).

임베딩 모델 다운로드 없이 scikit-learn TF-IDF 만으로 구현했다. 문서 수가 많아지면
OpenSearch/Vector DB로 교체 가능하도록 이 클래스의 public 메서드(``search``,
``lookup_compatibility``)만 Agent 쪽에서 사용하게 하여 구현 교체가 자유롭다.
"""

from __future__ import annotations

from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.models.compatibility import CompatibilityResult, CompatibilityStatus
from app.models.rag import RAGReference
from app.rag.ingestion import build_index


class RAGRetriever:
    def __init__(self, documents_dir: Path) -> None:
        self.documents_dir = documents_dir
        index = build_index(documents_dir)
        self._documents: list[dict] = index["documents"]
        self._chunks: list[dict] = index["chunks"]
        self._compat_entries: list[dict] = index["compatibility_entries"]
        self._deprecated_entries: list[dict] = index["deprecated_api_entries"]
        self.document_count = len(index["documents"])

        texts = [c["text"] for c in self._chunks]
        self._vectorizer: TfidfVectorizer | None = None
        self._matrix = None
        if texts:
            self._vectorizer = TfidfVectorizer()
            self._matrix = self._vectorizer.fit_transform(texts)

    def list_target_kubernetes_versions(self) -> list[str]:
        """Target Version 선택지 목록 (Section 18 UI).

        하드코딩 대신 ``rag/documents/release-notes/`` 에 Release Note 문서가
        존재하는 minor 버전만 후보로 노출한다 — RAG에 근거가 없는 버전을 목표로
        내걸면 Compatibility/Deprecated API 검사가 전부 UNKNOWN이 되어 버리므로,
        문서를 추가하는 것 자체가 "이 버전을 지원 목록에 추가"하는 행위가 된다.
        """
        minors: set[str] = set()
        for doc in self._documents:
            if doc.get("doc_type") != "release_note":
                continue
            minors.update(doc.get("applies_to_k8s", []))

        def _sort_key(v: str) -> tuple[int, int]:
            parts = v.split(".")
            return int(parts[0]), int(parts[1]) if len(parts) > 1 else 0

        return sorted(minors, key=_sort_key)

    def search(
        self,
        query: str,
        *,
        doc_type: str | None = None,
        component: str | None = None,
        top_k: int = 5,
    ) -> list[RAGReference]:
        if not self._chunks or self._vectorizer is None:
            return []
        candidate_idx = [
            i
            for i, c in enumerate(self._chunks)
            if (doc_type is None or c["doc_type"] == doc_type)
            and (component is None or (c["component"] or "").lower() == component.lower())
        ]
        if not candidate_idx:
            return []
        q_vec = self._vectorizer.transform([query])
        sims = cosine_similarity(q_vec, self._matrix[candidate_idx])[0]
        ranked = sorted(zip(candidate_idx, sims), key=lambda t: t[1], reverse=True)
        results: list[RAGReference] = []
        for idx, score in ranked[:top_k]:
            if score <= 0:
                continue
            c = self._chunks[idx]
            results.append(
                RAGReference(
                    document=c["document_title"],
                    section=c["section"],
                    doc_id=c["doc_id"],
                    excerpt=c["text"][:400],
                    score=round(float(score), 4),
                )
            )
        return results

    def lookup_compatibility(
        self,
        component: str,
        current_version: str | None,
        target_kubernetes_minor: str,
    ) -> CompatibilityResult:
        """No Hallucination 원칙(Section 25): 근거 없으면 반드시 UNKNOWN."""
        component_norm = component.lower()
        candidates = [
            e
            for e in self._compat_entries
            if e["component"].lower() == component_norm
            and e["target_kubernetes_minor"] == target_kubernetes_minor
        ]

        def _pattern_matches(entry: dict) -> bool:
            pattern = entry.get("current_version_pattern")
            if not pattern:
                return True
            if not current_version:
                return False
            return current_version.startswith(pattern)

        pattern_scoped = [e for e in candidates if e.get("current_version_pattern")]
        if pattern_scoped:
            matches = [e for e in candidates if _pattern_matches(e)]
        else:
            matches = candidates

        if not matches:
            return CompatibilityResult(
                component=component,
                current_version=current_version,
                target_kubernetes_version=target_kubernetes_minor,
                status=CompatibilityStatus.UNKNOWN,
                reason="RAG 문서에서 해당 컴포넌트/버전 조합에 대한 Compatibility 정보를 찾지 못했습니다.",
                recommendation="공식 Compatibility Matrix를 확인하여 수동으로 검증하세요 (Manual Verification Required).",
                sources=[],
            )

        entry = matches[0]
        return CompatibilityResult(
            component=component,
            current_version=current_version,
            target_kubernetes_version=target_kubernetes_minor,
            status=CompatibilityStatus(entry["status"]),
            reason=entry["reason"],
            recommendation=entry.get("recommendation"),
            sources=[
                RAGReference(
                    document=entry["document_title"],
                    section="compatibility_matrix",
                    doc_id=entry["doc_id"],
                )
            ],
        )

    def lookup_deprecated_api(self, kind: str, api_version: str) -> dict | None:
        """RAG에 등록된 Deprecated/Removed API 정보를 찾는다. 없으면 None (=UNKNOWN)."""
        for e in self._deprecated_entries:
            if e["kind"] == kind and e["api_version"] == api_version:
                return e
        return None
