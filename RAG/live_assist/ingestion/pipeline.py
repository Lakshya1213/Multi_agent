from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

from live_assist.core.config import get_settings
from live_assist.core.observability import observe
from live_assist.ingestion.chunker import chunk_pages, save_chunks
from live_assist.ingestion.indexer import index_chunks, rebuild_bm25_index
from live_assist.ingestion.parser import parse_pdf_pages
from live_assist.documents import paths

ProgressFn = Callable[[str, str], None]


def _noop(stage: str, message: str) -> None:
    pass


@observe(name="ingest_pdf_document")
def ingest_pdf(
    *,
    pdf_path: Path,
    user_id: str,
    document_id: str,
    source_filename: str,
    on_progress: ProgressFn = _noop,
) -> dict:
    """Run PDF ingestion outside the live meeting path."""

    settings = get_settings()
    started = time.perf_counter()
    try:
        on_progress("parse", f"Parsing {source_filename}")
        pages = parse_pdf_pages(pdf_path)
        if not pages:
            return {"status": "error", "error": "No extractable text found in PDF."}

        on_progress("chunk", f"Chunking {len(pages)} pages")
        chunks = chunk_pages(
            pages=pages,
            user_id=user_id,
            document_id=document_id,
            source_filename=source_filename,
            chunking_strategy=settings.rag_pipeline_name,
        )
        if settings.rag_enable_contextual_prefix:
            for chunk in chunks:
                chunk["text_with_context"] = (
                    f"Document: {source_filename}\n"
                    f"Page: {chunk['page']}\n\n{chunk['text']}"
                )
        chunk_path = paths.chunks_dir() / f"{user_id}_{document_id}.json"
        save_chunks(chunks, chunk_path)

        on_progress("index", f"Indexing {len(chunks)} chunks")
        index_result = index_chunks(
            chunks=chunks,
            collection_name=settings.rag_chroma_collection,
            embedding_model_name=settings.embedding_model,
        )

        on_progress("bm25", "Rebuilding BM25 index")
        bm25_result = rebuild_bm25_index(index_name=settings.rag_bm25_index_name)

        total_tokens = sum(int(chunk.get("token_count") or 0) for chunk in chunks)
        on_progress("done", "Ingestion complete")
        return {
            "status": "ok",
            "chunk_count": len(chunks),
            "total_tokens": total_tokens,
            "elapsed_seconds": round(time.perf_counter() - started, 3),
            "index": index_result,
            "bm25": bm25_result,
        }
    except Exception as exc:
        return {
            "status": "error",
            "error": f"{type(exc).__name__}: {exc}",
            "elapsed_seconds": round(time.perf_counter() - started, 3),
        }

