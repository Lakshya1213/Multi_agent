from agents.rag_agent import rag_agent


def rag_node(state):
    """
    Run RAG for customer turns selected by speaker_node.
    """

    speaker = (state.get("speaker") or "").lower()

    state["rag"] = rag_agent(
        state.get("transcript", ""),
        speaker=speaker,
        session_id=state.get("session_id"),
    )

    state["rag_answer"] = state["rag"].get("answer", "")
    state["rag_context"] = state["rag"].get("context", "")
    state["rag_top_chunks"] = state["rag"].get("top_chunks", [])
    state["rag_metadata"] = state["rag"].get("metadata", {})

    return state
