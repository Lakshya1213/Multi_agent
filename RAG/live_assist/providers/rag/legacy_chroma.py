from __future__ import annotations

import time
from typing import Any

from live_assist.providers.rag.base import RetrievalResult
from live_assist.providers.rag.chroma import ChromaDBRetriever


class LegacyChromaRetriever:
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.retriever = ChromaDBRetriever(config)

    def retrieve(
        self,
        *,
        query: str,
        user_id: str,
        filters: dict[str, Any] | None = None,
    ) -> RetrievalResult:
        started = time.perf_counter()
        product_filter = None
        if filters and filters.get("product"):
            product_filter = {"product": filters["product"]}
        results = self.retriever.hybrid_search(
            query=query,
            k=int(self.config["NUMBER_OF_CHUNKS_TO_RETRIVE"]),
            alpha=float(self.config["WEIGHTAGE_OF_VECTOR_SIMILARITY"]),
            filter_dict=product_filter,
        )
        return RetrievalResult(
            context="\n\n".join(doc.page_content for doc, _ in results),
            rag_top_chunks=[doc.page_content for doc, _ in results[:3]],
            raw_chunks=[
                {"text": doc.page_content, "metadata": doc.metadata, "score": score}
                for doc, score in results
            ],
            duration_ms=(time.perf_counter() - started) * 1000,
            metadata={"provider": "legacy_chroma"},
        )

