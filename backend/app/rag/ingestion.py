"""rag/documents/**/*.md 를 파싱해 검색용 Chunk와 Compatibility Entry로 변환한다.

문서 추가만으로 검색 결과에 반영되도록(코드 수정 불필요, Section 9), 이 모듈은
어떤 컴포넌트/버전 조합이 존재하는지 전혀 모른 채 오직 파일 구조(frontmatter,
``## 섹션``, ` ```yaml compatibility_matrix ``` ` 블록)만 안다.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

import yaml

from app.models.rag import RAGDocumentMeta, RAGDocumentType

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?(.*)$", re.DOTALL)
_YAML_BLOCK_RE = re.compile(r"```yaml\s*\n(.*?)```", re.DOTALL)
_SECTION_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)


@dataclass
class Chunk:
    doc_id: str
    document_title: str
    section: str
    text: str
    doc_type: str
    component: str | None
    applies_to_k8s: list[str]
    tags: list[str]
    path: str


@dataclass
class DeprecatedAPIEntry:
    kind: str
    api_version: str
    deprecated_in_version: str | None
    removed_in_version: str | None
    replacement_api_version: str | None
    notes: str
    doc_id: str
    document_title: str
    path: str


@dataclass
class CompatibilityEntry:
    component: str
    current_version_pattern: str | None
    target_kubernetes_minor: str
    status: str
    reason: str
    recommendation: str | None
    doc_id: str
    document_title: str
    path: str


def parse_document(path: Path) -> tuple[RAGDocumentMeta, str]:
    text = path.read_text(encoding="utf-8")
    m = _FRONTMATTER_RE.match(text)
    if not m:
        raise ValueError(f"frontmatter(--- ... ---)가 없는 RAG 문서: {path}")
    meta_raw = yaml.safe_load(m.group(1)) or {}
    body = m.group(2)
    meta = RAGDocumentMeta(
        doc_id=meta_raw["doc_id"],
        title=meta_raw["title"],
        doc_type=RAGDocumentType(meta_raw["doc_type"]),
        component=meta_raw.get("component"),
        applies_to_k8s=[str(v) for v in meta_raw.get("applies_to_k8s", [])],
        tags=[str(v) for v in meta_raw.get("tags", [])],
        path=str(path),
    )
    return meta, body


def chunk_body(meta: RAGDocumentMeta, body: str) -> list[Chunk]:
    positions = [(m.start(), m.group(1).strip()) for m in _SECTION_RE.finditer(body)]
    chunks: list[Chunk] = []

    def make(section: str, text: str) -> Chunk:
        return Chunk(
            doc_id=meta.doc_id,
            document_title=meta.title,
            section=section,
            text=text,
            doc_type=meta.doc_type.value,
            component=meta.component,
            applies_to_k8s=meta.applies_to_k8s,
            tags=meta.tags,
            path=meta.path,
        )

    if not positions:
        text = body.strip()
        return [make(meta.title, text)] if text else []

    if positions[0][0] > 0:
        intro = body[: positions[0][0]].strip()
        if intro:
            chunks.append(make("개요", intro))

    for i, (start, title) in enumerate(positions):
        end = positions[i + 1][0] if i + 1 < len(positions) else len(body)
        section_text = _SECTION_RE.sub("", body[start:end], count=1).strip()
        if section_text:
            chunks.append(make(title, section_text))
    return chunks


def extract_compatibility_entries(meta: RAGDocumentMeta, body: str) -> list[CompatibilityEntry]:
    entries: list[CompatibilityEntry] = []
    for block_match in _YAML_BLOCK_RE.finditer(body):
        block_text = block_match.group(1)
        if "compatibility_matrix" not in block_text:
            continue
        data = yaml.safe_load(block_text) or {}
        cm = data.get("compatibility_matrix")
        if not cm:
            continue
        component = cm.get("component", meta.component)
        pattern = cm.get("current_version_pattern")
        for e in cm.get("entries", []):
            entries.append(
                CompatibilityEntry(
                    component=component,
                    current_version_pattern=pattern,
                    target_kubernetes_minor=str(e["target_kubernetes_minor"]),
                    status=e["status"],
                    reason=e.get("reason", ""),
                    recommendation=e.get("recommendation"),
                    doc_id=meta.doc_id,
                    document_title=meta.title,
                    path=meta.path,
                )
            )
    return entries


def extract_deprecated_api_entries(meta: RAGDocumentMeta, body: str) -> list[DeprecatedAPIEntry]:
    entries: list[DeprecatedAPIEntry] = []
    for block_match in _YAML_BLOCK_RE.finditer(body):
        block_text = block_match.group(1)
        if "deprecated_api_guide" not in block_text:
            continue
        data = yaml.safe_load(block_text) or {}
        guide = data.get("deprecated_api_guide")
        if not guide:
            continue
        for e in guide.get("entries", []):
            entries.append(
                DeprecatedAPIEntry(
                    kind=e["kind"],
                    api_version=e["api_version"],
                    deprecated_in_version=str(e["deprecated_in_version"]) if e.get("deprecated_in_version") else None,
                    removed_in_version=str(e["removed_in_version"]) if e.get("removed_in_version") else None,
                    replacement_api_version=e.get("replacement_api_version"),
                    notes=e.get("notes", ""),
                    doc_id=meta.doc_id,
                    document_title=meta.title,
                    path=meta.path,
                )
            )
    return entries


def load_documents_dir(
    documents_dir: Path,
) -> tuple[list[RAGDocumentMeta], list[Chunk], list[CompatibilityEntry], list[DeprecatedAPIEntry]]:
    metas: list[RAGDocumentMeta] = []
    chunks: list[Chunk] = []
    compat_entries: list[CompatibilityEntry] = []
    deprecated_entries: list[DeprecatedAPIEntry] = []
    for path in sorted(documents_dir.rglob("*.md")):
        if path.name.upper() == "README.MD":
            continue  # 안내 문서는 색인 대상이 아님
        meta, body = parse_document(path)
        metas.append(meta)
        chunks.extend(chunk_body(meta, body))
        compat_entries.extend(extract_compatibility_entries(meta, body))
        deprecated_entries.extend(extract_deprecated_api_entries(meta, body))
    return metas, chunks, compat_entries, deprecated_entries


def build_index(documents_dir: Path) -> dict:
    metas, chunks, compat_entries, deprecated_entries = load_documents_dir(documents_dir)
    return {
        "documents": [m.model_dump(mode="json") for m in metas],
        "chunks": [asdict(c) for c in chunks],
        "compatibility_entries": [asdict(e) for e in compat_entries],
        "deprecated_api_entries": [asdict(e) for e in deprecated_entries],
    }


def build_and_save_index(documents_dir: Path, index_path: Path) -> dict:
    index = build_index(documents_dir)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    return index
