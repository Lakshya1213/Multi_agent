from agents.checklist_agent import checklist_agent


def checklist_node(state):
    """
    This node updates checklist for the active stage.

    It reads:
    - active_stage
    - transcript
    - checklist_status_by_stage

    It writes:
    - checklist
    - checklist_status_by_stage
    - next_best_question
    - stage_completed
    """

    active_stage = state.get("active_stage")
    transcript = state.get("transcript")

    checklist_status_by_stage = state.get("checklist_status_by_stage", {})

    current_stage_status = checklist_status_by_stage.get(active_stage, {})

    checklist_result = checklist_agent(
        stage=active_stage,
        transcript=transcript,
        current_status=current_stage_status
    )

    state["checklist"] = checklist_result

    checklist_status_by_stage[active_stage] = checklist_result.get(
        "final_status",
        checklist_result.get("updated_status", current_stage_status)
    )

    state["checklist_status_by_stage"] = checklist_status_by_stage

    state["next_best_question"] = checklist_result.get("next_best_question")

    completion_percent = checklist_result.get("completion_percent", 0)
    state["stage_completed"] = completion_percent == 100

    return state