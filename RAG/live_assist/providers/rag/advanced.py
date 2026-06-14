from __future__ import annotations

import time
from typing import Any

from live_assist.core.config import Settings
from live_assist.core.observability import observe
from live_assist.providers.rag.base import RetrievalResult
from live_assist.retrieval.advanced_search import (
    bm25_search,
    reciprocal_rank_fusion,
    rerank_local,
    semantic_search,
)


class AdvancedRetriever:
    def __init__(self, settings: Settings):
        self.settings = settings

    def _filters(self, user_id: str, filters: dict[str, Any] | None) -> dict[str, Any]:
        output: dict[str, Any] = {"chunking_strategy": self.settings.rag_pipeline_name}
        if self.settings.rag_user_scope_enabled:
            output["user_id"] = user_id
        if filters:
            for key in ("document_id", "source_filename"):
                if filters.get(key):
                    output[key] = filters[key]
        return output

    @observe(name="advanced_rag_retrieve")
    def retrieve(
        self,
        *,
        query: str,
        user_id: str,
        filters: dict[str, Any] | None = None,
    ) -> RetrievalResult:
        started = time.perf_counter()
        effective_filters = self._filters(user_id, filters)
        try:
            mode = self.settings.rag_retrieval_mode
            top_k = self.settings.rag_top_k
            candidate_limit = max(self.settings.rag_candidate_limit, top_k)
            semantic_results: list[dict[str, Any]] = []
            bm25_results: list[dict[str, Any]] = []

            if mode in {"semantic", "hybrid", "reranked"}:
                semantic_results = semantic_search(
                    query=query,
                    collection_name=self.settings.rag_chroma_collection,
                    embedding_model_name=self.settings.embedding_model,
                    limit=candidate_limit if mode in {"hybrid", "reranked"} else top_k,
                    filters=effective_filters,
                )
            if mode in {"bm25", "hybrid", "reranked"}:
                bm25_results = bm25_search(
                    query=query,
                    index_name=self.settings.rag_bm25_index_name,
                    limit=candidate_limit if mode in {"hybrid", "reranked"} else top_k,
                    filters=effective_filters,
                )

            if mode == "semantic":
                chunks = semantic_results[:top_k]
            elif mode == "bm25":
                chunks = bm25_results[:top_k]
            else:
                chunks = reciprocal_rank_fusion(
                    {"semantic": semantic_results, "bm25": bm25_results},
                    limit=candidate_limit if mode == "reranked" else top_k,
                )
                if mode == "reranked" and self.settings.rag_rerank_provider == "local":
                    chunks = rerank_local(
                        query,
                        chunks,
                        model_name=self.settings.rag_rerank_model,
                        top_k=top_k,
                    )
                else:
                    chunks = chunks[:top_k]

            context_parts = []
            top_chunks = []
            for chunk in chunks:
                text = chunk.get("text_with_context") or chunk.get("text") or ""
                if not text:
                    continue
                header = f"[{chunk.get('source_filename', '')} | p{chunk.get('page', '')}]"
                context_parts.append(f"{header}\n{text}")
                if len(top_chunks) < 3:
                    top_chunks.append(text)

            return RetrievalResult(
                context="\n\n".join(context_parts),
                rag_top_chunks=top_chunks,
                raw_chunks=chunks,
                duration_ms=(time.perf_counter() - started) * 1000,
                metadata={
                    "provider": "advanced",
                    "mode": mode,
                    "filters": effective_filters,
                    "semantic_count": len(semantic_results),
                    "bm25_count": len(bm25_results),
                },
            )
        except Exception as exc:
            return RetrievalResult(
                duration_ms=(time.perf_counter() - started) * 1000,
                metadata={"provider": "advanced", "error": f"{type(exc).__name__}: {exc}"},
            )
