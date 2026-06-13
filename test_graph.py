from graph.workflow import build_live_assist_graph
import json


graph = build_live_assist_graph()

previous_stage = None
checklist_status_by_stage = {}
conversation_window = []

examples = [
    {
        "speaker": "advisor",
        "text": "Good afternoon, this is Mahesh calling from Fin Ideas. I wanted to speak with Joicy, sir."
    },
    {
        "speaker": "customer",
        "text": "I have been investing in stocks for the last 8 years."
    },
    {
        "speaker": "customer",
        "text": "I currently have a portfolio of around 2 crore rupees."
    },
    {
        "speaker": "customer",
        "text": "What is NIFTY ETF and how hedging works?"
    },
    {
        "speaker": "customer",
        "text": "What are your advisory charges and brokerage?"
    }
]


with open("langgraph_trace.txt", "w", encoding="utf-8") as f:

    for idx, item in enumerate(examples, start=1):

        speaker = item["speaker"]
        transcript = item["text"]

        initial_state = {
            "speaker": speaker,
            "transcript": transcript,

            "previous_stage": previous_stage,
            "previous_stage_before_detection": None,

            "checklist_status_by_stage": checklist_status_by_stage,
            "conversation_window": conversation_window,

            "stage_detection": None,
            "active_stage": None,

            "checklist": None,
            "stage_completed": False,
            "next_best_question": None,

            "stage_pitch": None,
            "suggested_question": None,

            "llm_usage": None,
            "result": None
        }

        final_state = graph.invoke(initial_state)

        result = {
            "stage_detection": final_state.get("stage_detection"),
            "active_stage": final_state.get("active_stage"),
            "stage_completed": final_state.get("stage_completed"),
            "checklist": final_state.get("checklist"),
            "stage_pitch": final_state.get("stage_pitch"),
            "suggested_question": final_state.get("suggested_question"),
            "checklist_status_by_stage": final_state.get("checklist_status_by_stage"),
            "next_best_question": final_state.get("next_best_question"),
            "conversation_window": final_state.get("conversation_window"),
            "llm_usage": final_state.get("llm_usage")
        }

        f.write("=" * 70 + "\n")
        f.write(f"EXAMPLE #{idx}\n")
        f.write(f"Speaker: {speaker}\n")
        f.write(f"Transcript: {transcript}\n\n")

        f.write("RESULT:\n")
        f.write(json.dumps(result, indent=2, ensure_ascii=False))
        f.write("\n\n")

        f.write(f"Current Stage: {final_state.get('active_stage')}\n")
        f.write(f"Stage Completed: {final_state.get('stage_completed')}\n")
        f.write(f"Next Question: {final_state.get('next_best_question')}\n")

        if final_state.get("stage_pitch"):
            f.write("Stage Pitch:\n")
            f.write(
                json.dumps(
                    final_state.get("stage_pitch"),
                    indent=2,
                    ensure_ascii=False
                )
            )
            f.write("\n")

        if final_state.get("suggested_question"):
            f.write(f"Suggested Question: {final_state.get('suggested_question')}\n")

        f.write("\n\n")

        previous_stage = final_state.get("active_stage")
        checklist_status_by_stage = final_state.get("checklist_status_by_stage", {})
        conversation_window = final_state.get("conversation_window", [])

        print(f"Processed example {idx}/{len(examples)}")


print("\nOutput saved to langgraph_trace.txt")