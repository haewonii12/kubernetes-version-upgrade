#!/usr/bin/env python3
"""RAG 문서 색인 미리보기/검증 CLI.

    cd rag/ingestion && python3 build_index.py

rag/documents/**/*.md 를 파싱해 rag/index/index.json 에 저장하고, 문서/청크/
Compatibility Entry 개수를 출력한다. Retriever는 서버 기동 시 항상 문서를
새로 파싱하므로 이 스크립트는 필수 실행 단계는 아니고, 새 문서를 추가한 뒤
frontmatter/YAML 블록 문법 오류를 미리 확인하는 용도다 (Section 9).
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.rag.ingestion import build_and_save_index  # noqa: E402

DOCUMENTS_DIR = REPO_ROOT / "rag" / "documents"
INDEX_PATH = REPO_ROOT / "rag" / "index" / "index.json"


def main() -> None:
    index = build_and_save_index(DOCUMENTS_DIR, INDEX_PATH)
    print(f"문서 {len(index['documents'])}개, 청크 {len(index['chunks'])}개, "
          f"Compatibility Entry {len(index['compatibility_entries'])}개 색인 완료")
    print(f"저장 위치: {INDEX_PATH}")


if __name__ == "__main__":
    main()
