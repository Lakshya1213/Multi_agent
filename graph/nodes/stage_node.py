from agents.call_stage_agent import detect_stage, update_conversation_window


def stage_node(state):
    old_stage = state.get("previous_stage")

    stage_result = detect_stage(
        transcript=state["transcript"],
        previous_stage=old_stage,
        conversation_window=state.get("conversation_window", [])
    )

    state["stage_detection"] = stage_result
    state["previous_stage_before_detection"] = old_stage

    detected_stage = stage_result.get("stage")

    if stage_result.get("transition_allowed", True):
        active_stage = detected_stage
    else:
        active_stage = old_stage or detected_stage

    state["active_stage"] = active_stage
    state["previous_stage"] = active_stage

    state["conversation_window"] = update_conversation_window(
        conversation_window=state.get("conversation_window", []),
        speaker=state.get("speaker"),
        text=state.get("transcript"),
        stage=active_stage,
        max_turns=5
    )

    return state