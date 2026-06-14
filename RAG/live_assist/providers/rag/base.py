from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class RetrievalResult:
    context: str = ""
    rag_top_chunks: list[str] = field(default_factory=list)
    raw_chunks: list[dict[str, Any]] = field(default_factory=list)
    duration_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class Retriever(Protocol):
    def retrieve(
        self,
        *,
        query: str,
        user_id: str,
        filters: dict[str, Any] | None = None,
    ) -> RetrievalResult:
        ...

