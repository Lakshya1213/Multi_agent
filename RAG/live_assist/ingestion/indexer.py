from __future__ import annotations

import json
import pickle
from pathlib import Path
from typing import Any

import chromadb
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

from live_assist.documents import paths


def _clean_metadata(chunk: dict[str, Any]) -> dict[str, Any]:
    metadata = {}
    for key, value in chunk.items():
        if key in {"text", "text_with_context"} or value is None:
            continue
        if isinstance(value, (str, int, float, bool)):
            metadata[key] = value
        else:
            metadata[key] = json.dumps(value, ensure_ascii=True)
    return metadata


def index_chunks(
    *,
    chunks: list[dict],
    collection_name: str,
    embedding_model_name: str,
) -> dict[str, int]:
    """Embed and upsert chunks into the advanced Chroma collection."""

    if not chunks:
        return {"indexed": 0, "failed": 0}

    model = SentenceTransformer(embedding_model_name)
    texts = [chunk.get("text_with_context") or chunk["text"] for chunk in chunks]
    embeddings = model.encode(texts).tolist()
    client = chromadb.PersistentClient(path=str(paths.chroma_dir()))
    collection = client.get_or_create_collection(name=collection_name)
    collection.upsert(
        ids=[chunk["chunk_id"] for chunk in chunks],
        documents=texts,
        metadatas=[_clean_metadata(chunk) for chunk in chunks],
        embeddings=embeddings,
    )
    return {"indexed": len(chunks), "failed": 0}


def rebuild_bm25_index(*, index_name: str) -> dict[str, int]:
    """Rebuild a BM25 index over all saved user document chunks."""

    docs: list[dict] = []
    for path in paths.chunks_dir().glob("*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            docs.extend(payload.get("chunks", []))
        except Exception:
            continue

    index_path = paths.bm25_dir() / f"{index_name}.pkl"
    docs_path = paths.bm25_dir() / f"{index_name}.docs.json"
    corpus = [
        (chunk.get("text_with_context") or chunk.get("text") or "").lower().split()
        for chunk in docs
    ]
    bm25 = BM25Okapi(corpus or [[""]])
    with index_path.open("wb") as f:
        pickle.dump(bm25, f)
    docs_path.write_text(json.dumps(docs, ensure_ascii=True), encoding="utf-8")
    return {"chunk_count": len(docs), "docs": len({doc.get("document_id") for doc in docs})}

