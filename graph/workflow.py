from langgraph.graph import StateGraph, END

from graph.state import LiveAssistState
from graph.nodes.stage_node import stage_node
from graph.nodes.checklist_node import checklist_node
from graph.nodes.stage_pitch_node import stage_pitch_node
from graph.nodes.question_node import question_node


def route_after_checklist(state):
    """
    Decide what to do after checklist update.
    If stage changed, generate stage pitch.
    If stage not changed, suggest next checklist question.
    """

    previous_stage = state.get("previous_stage_before_detection")
    active_stage = state.get("active_stage")

    if previous_stage is not None and previous_stage != active_stage:
        return "stage_pitch_node"

    return "question_node"


def build_live_assist_graph():
    workflow = StateGraph(LiveAssistState)

    workflow.add_node("stage_node", stage_node)
    workflow.add_node("checklist_node", checklist_node)
    workflow.add_node("stage_pitch_node", stage_pitch_node)
    workflow.add_node("question_node", question_node)

    workflow.set_entry_point("stage_node")

    workflow.add_edge("stage_node", "checklist_node")

    workflow.add_conditional_edges(
        "checklist_node",
        route_after_checklist,
        {
            "stage_pitch_node": "stage_pitch_node",
            "question_node": "question_node"
        }
    )

    workflow.add_edge("stage_pitch_node", END)
    workflow.add_edge("question_node", END)

    return workflow.compile()