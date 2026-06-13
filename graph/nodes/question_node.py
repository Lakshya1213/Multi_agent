def question_node(state):
    """
    This node gives next question when stage is not changed.
    It uses checklist next_best_question.
    """

    checklist_result = state.get("checklist", {})

    state["stage_pitch"] = None

    state["suggested_question"] = checklist_result.get(
        "next_best_question",
        "Continue the conversation based on the current checklist."
    )

    return state