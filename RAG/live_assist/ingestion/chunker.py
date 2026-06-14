from __future__ import annotations

import re
from pathlib import Path


def _token_count(text: str) -> int:
    return len(text.split())


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def chunk_pages(
    *,
    pages: list[dict],
    user_id: str,
    document_id: str,
    source_filename: str,
    chunking_strategy: str,
    max_tokens: int = 350,
    overlap_tokens: int = 50,
) -> list[dict]:
    """Create simple overlapping chunks from parsed PDF pages."""

    chunks: list[dict] = []
    chunk_index = 0
    for page in pages:
        words = _clean_text(str(page["text"])).split()
        if not words:
            continue

        start = 0
        while start < len(words):
            end = min(start + max_tokens, len(words))
            text = " ".join(words[start:end]).strip()
            if text:
                chunk_index += 1
                chunk_id = f"{document_id}_chunk_{chunk_index:04d}"
                chunks.append(
                    {
                        "chunk_id": chunk_id,
                        "user_id": user_id,
                        "document_id": document_id,
                        "source_filename": source_filename,
                        "chunking_strategy": chunking_strategy,
                        "page": int(page["page"]),
                        "section": "",
                        "token_count": _token_count(text),
                        "text": text,
                        "text_with_context": text,
                    }
                )
            if end >= len(words):
                break
            start = max(end - overlap_tokens, start + 1)
    return chunks


def save_chunks(chunks: list[dict], output_path: Path) -> None:
    import json

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps({"chunks": chunks}, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )

