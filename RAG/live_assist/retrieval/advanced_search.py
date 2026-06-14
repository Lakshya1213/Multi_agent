from __future__ import annotations

import json
import pickle
from collections import defaultdict
from pathlib import Path
from typing import Any

import chromadb
import numpy as np
from sentence_transformers import SentenceTransformer

from live_assist.documents import paths


def _matches_filters(chunk: dict[str, Any], filters: dict[str, Any]) -> bool:
    return all(str(chunk.get(key, "")) == str(value) for key, value in filters.items())


def _to_chroma_where(filters: dict[str, Any]) -> dict[str, Any] | None:
    clauses = [{key: value} for key, value in filters.items() if value is not None]
    if not clauses:
        return None
    if len(clauses) == 1:
        return clauses[0]
    return {"$and": clauses}


def semantic_search(
    *,
    query: str,
    collection_name: str,
    embedding_model_name: str,
    limit: int,
    filters: dict[str, Any],
) -> list[dict[str, Any]]:
    model = SentenceTransformer(embedding_model_name)
    embedding = model.encode(query).tolist()
    collection = chromadb.PersistentClient(path=str(paths.chroma_dir())).get_or_create_collection(
        name=collection_name
    )
    results = collection.query(
        query_embeddings=[embedding],
        n_results=max(limit, 1),
        where=_to_chroma_where(filters),
        include=["documents", "metadatas", "distances"],
    )
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]
    output = []
    for text, metadata, distance in zip(documents, metadatas, distances):
        output.append(
            {
                **(metadata or {}),
                "text": text,
                "score": 1 / (1 + float(distance)),
                "source": "semantic",
            }
        )
    return output


def bm25_search(*, query: str, index_name: str, limit: int, filters: dict[str, Any]) -> list[dict[str, Any]]:
    index_path = paths.bm25_dir() / f"{index_name}.pkl"
    docs_path = paths.bm25_dir() / f"{index_name}.docs.json"
    if not index_path.exists() or not docs_path.exists():
        return []
    with index_path.open("rb") as f:
        bm25 = pickle.load(f)
    docs = json.loads(docs_path.read_text(encoding="utf-8"))
    scores = bm25.get_scores(query.lower().split())
    if len(scores) == 0:
        return []
    max_score = float(np.max(scores)) or 1.0
    candidates = []
    for chunk, score in zip(docs, scores):
        if not _matches_filters(chunk, filters):
            continue
        candidates.append(
            {
                **chunk,
                "score": float(score) / max_score,
                "source": "bm25",
            }
        )
    candidates.sort(key=lambda item: item["score"], reverse=True)
    return candidates[:limit]


def reciprocal_rank_fusion(
    ranked_lists: dict[str, list[dict[str, Any]]],
    *,
    limit: int,
    rrf_k: int = 60,
) -> list[dict[str, Any]]:
    scores: dict[str, float] = defaultdict(float)
    payloads: dict[str, dict[str, Any]] = {}
    sources: dict[str, set[str]] = defaultdict(set)
    for source, results in ranked_lists.items():
        for rank, item in enumerate(results, start=1):
            chunk_id = str(item.get("chunk_id"))
            scores[chunk_id] += 1 / (rrf_k + rank)
            payloads.setdefault(chunk_id, item)
            sources[chunk_id].add(source)
    ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)[:limit]
    output = []
    for rank, (chunk_id, score) in enumerate(ordered, start=1):
        item = dict(payloads[chunk_id])
        item["score"] = float(score)
        item["sources"] = sorted(sources[chunk_id])
        item["final_rank"] = rank
        output.append(item)
    return output


def rerank_local(query: str, candidates: list[dict[str, Any]], *, model_name: str, top_k: int) -> list[dict[str, Any]]:
    if not candidates:
        return []
    from sentence_transformers import CrossEncoder

    model = CrossEncoder(model_name)
    pairs = [[query, item.get("text", "")] for item in candidates]
    scores = model.predict(pairs)
    for item, score in zip(candidates, scores):
        item["rerank_score"] = float(score)
    candidates.sort(key=lambda item: item.get("rerank_score", 0), reverse=True)
    return candidates[:top_k]
