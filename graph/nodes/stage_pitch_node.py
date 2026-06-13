from agents.sales_call_agent import generate_stage_pitch


def stage_pitch_node(state):
    previous_stage = state.get("previous_stage_before_detection")
    active_stage = state.get("active_stage")
    transcript = state.get("transcript")
    checklist_result = state.get("checklist", {})

    stage_pitch = None

    if previous_stage is not None and previous_stage != active_stage:
        stage_pitch = generate_stage_pitch(
            previous_stage=previous_stage,
            current_stage=active_stage,
            transcript=transcript,
            checklist_result=checklist_result
        )

    state["stage_pitch"] = stage_pitch

    return state