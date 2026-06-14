from __future__ import annotations

import os
import sys
import uuid
from typing import Any


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAG_ROOT = os.path.join(PROJECT_ROOT, "RAG")

if RAG_ROOT not in sys.path:
    sys.path.append(RAG_ROOT)


def rag_agent(
    query: str,
    *,
    speaker: str = "customer",
    session_id: str | None = None,
) -> dict[str, Any]:
    """
    Adapter from the main graph to the existing RAG/live_assist workflow.

    RAG is optional in the main graph. If the RAG index, dependencies, or API
    keys are not ready, this returns a failed RAG payload instead of breaking
    the existing stage/checklist flow.
    """

    clean_query = (query or "").strip()
    if not clean_query:
        return {
            "status": "skipped",
            "answer": "",
            "context": "",
            "top_chunks": [],
            "metadata": {"reason": "empty_query"},
        }

    try:
        from RAG.live_assist.core.models import Speaker
        from RAG.live_assist.live_cycle.service import _invoke_turn_workflow

        normalized_speaker = Speaker.CUSTOMER
        if (speaker or "").lower() in {"advisor", "manager", "worker", "agent"}:
            normalized_speaker = Speaker.WORKER

        response = _invoke_turn_workflow(
            session_id=session_id or f"main_graph_{uuid.uuid4().hex}",
            speaker=normalized_speaker,
            text=clean_query,
            manual_question=True,
        )

        return {
            "status": "ok",
            "answer": response.get("answer", ""),
            "context": response.get("context", ""),
            "top_chunks": response.get("rag_top_chunks", []),
            "metadata": {
                "route": response.get("route", ""),
                "product": response.get("product", ""),
                "product_context": response.get("product_context", ""),
                "enriched_query": response.get("rewriten_question", ""),
                "retrieve_duration_ms": response.get("rag_retrieve_duration_ms", 0.0),
                "generation_duration_ms": response.get("generation_duration_ms", 0.0),
            },
        }
    except Exception as exc:
        return {
            "status": "failed",
            "answer": "",
            "context": "",
            "top_chunks": [],
            "metadata": {
                "error_type": type(exc).__name__,
                "error": str(exc) or repr(exc),
            },
        }
