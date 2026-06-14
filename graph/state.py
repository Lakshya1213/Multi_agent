from typing import TypedDict, Optional, Dict, Any, List


class LiveAssistState(TypedDict):
    # ----------------------
    # Input
    # ----------------------

    speaker: str
    transcript: str
    speaker_route: Optional[str]

    # ----------------------
    # Memory
    # ----------------------

    previous_stage: Optional[str]

    # Needed by stage_pitch_node
    previous_stage_before_detection: Optional[str]

    checklist_status_by_stage: Dict[str, Any]
    conversation_window: List[Dict[str, Any]]
    session_id: Optional[str]

    # ----------------------
    # Stage Node Output
    # ----------------------

    stage_detection: Optional[Dict[str, Any]]
    active_stage: Optional[str]

    # ----------------------
    # Checklist Node Output
    # ----------------------

    checklist: Optional[Dict[str, Any]]
    stage_completed: bool
    next_best_question: Optional[str]

    # ----------------------
    # RAG Node Output
    # ----------------------

    rag: Optional[Dict[str, Any]]
    rag_answer: Optional[str]
    rag_context: Optional[str]
    rag_top_chunks: List[str]
    rag_metadata: Optional[Dict[str, Any]]

    # ----------------------
    # Stage Pitch Node Output
    # ----------------------

    stage_pitch: Optional[Dict[str, Any]]
    suggested_question: Optional[str]

    # ----------------------
    # Final Output
    # ----------------------

    llm_usage: Optional[Dict[str, Any]]
    result: Optional[Dict[str, Any]]
