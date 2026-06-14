ADVISOR_HINTS = (
    "good morning",
    "good afternoon",
    "good evening",
    "this is",
    "calling from",
    "wanted to speak",
    "may i speak",
    "can i speak",
    "fin ideas",
    "finideas",
)

CUSTOMER_HINTS = (
    "i have",
    "i am",
    "i currently",
    "i want",
    "i need",
    "my portfolio",
    "my investment",
    "what is",
    "what are",
    "how",
    "charges",
    "brokerage",
    "hedging",
    "nifty",
    "etf",
)


def detect_speaker_from_text(text):
    """
    Lightweight fallback speaker detection for plain transcript turns.
    """

    lower_text = (text or "").strip().lower()

    if lower_text.startswith("advisor:"):
        return "advisor"

    if lower_text.startswith("customer:"):
        return "customer"

    advisor_score = sum(1 for hint in ADVISOR_HINTS if hint in lower_text)
    customer_score = sum(1 for hint in CUSTOMER_HINTS if hint in lower_text)

    if customer_score > advisor_score:
        return "customer"

    if advisor_score > customer_score:
        return "advisor"

    # In this live-assist setup, unknown turns should not call RAG by default.
    return "advisor"


def speaker_node(state):
    """
    Normalize or infer the current turn speaker before routing.
    """

    speaker = (state.get("speaker") or "").strip().lower()

    if speaker in {"", "auto", "unknown", "speaker"}:
        speaker = detect_speaker_from_text(state.get("transcript", ""))
        state["speaker"] = speaker

    if speaker == "customer":
        state["speaker_route"] = "rag_node"
    else:
        state["speaker_route"] = "stage_node"

    return state
