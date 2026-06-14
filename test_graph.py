from graph.workflow import build_live_assist_graph
import json

app = build_live_assist_graph()

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

previous_stage = None
checklist_status_by_stage = {}
conversation_window = []

all_results = []

for index, item in enumerate(examples, start=1):
    state = {
        "speaker": item["speaker"],
        "transcript": item["text"],
        "speaker_route": None,

        "previous_stage": previous_stage,
        "previous_stage_before_detection": None,

        "checklist_status_by_stage": checklist_status_by_stage,
        "conversation_window": conversation_window,
        "session_id": "example_test_session",

        "stage_detection": None,
        "active_stage": None,

        "checklist": None,
        "stage_completed": False,
        "next_best_question": None,

        "rag": None,
        "rag_answer": None,
        "rag_context": None,
        "rag_top_chunks": [],
        "rag_metadata": None,

        "stage_pitch": None,
        "suggested_question": None,

        "llm_usage": None,
        "result": None,
    }

    result = app.invoke(state)

    print("=" * 80)
    print("TURN:", index)
    print("Speaker:", result.get("speaker"))
    print("Route:", result.get("speaker_route"))
    print("Text:", item["text"])
    print("Active stage:", result.get("active_stage"))
    print("Previous stage:", result.get("previous_stage_before_detection"))
    print("RAG answer:", result.get("rag_answer"))
    print("Stage pitch:", result.get("stage_pitch"))
    print("Next question:", result.get("next_best_question"))
    print("Suggested question:", result.get("suggested_question"))

    turn_output = {
        "turn": index,
        "speaker": result.get("speaker"),
        "route": result.get("speaker_route"),
        "text": item["text"],
        "previous_stage": result.get("previous_stage_before_detection"),
        "active_stage": result.get("active_stage"),
        "rag_answer": result.get("rag_answer"),
        "rag_status": (result.get("rag") or {}).get("status"),
        "rag_metadata": result.get("rag_metadata"),
        "stage_pitch": result.get("stage_pitch"),
        "next_question": result.get("next_best_question"),
        "suggested_question": result.get("suggested_question"),
        "stage_completed": result.get("stage_completed"),
        "checklist": result.get("checklist"),
        "llm_usage": result.get("llm_usage"),
    }

    all_results.append(turn_output)

    previous_stage = result.get("active_stage")
    checklist_status_by_stage = result.get("checklist_status_by_stage", {})
    conversation_window = result.get("conversation_window", [])

with open("live_assist_output.json", "w", encoding="utf-8") as f:
    json.dump(all_results, f, indent=4, ensure_ascii=False, default=str)

with open("live_assist_output.txt", "w", encoding="utf-8") as f:
    for item in all_results:
        f.write("=" * 80 + "\n")
        f.write(f"TURN: {item['turn']}\n")
        f.write(f"Speaker: {item['speaker']}\n")
        f.write(f"Route: {item['route']}\n")
        f.write(f"Text: {item['text']}\n")
        f.write(f"Previous Stage: {item['previous_stage']}\n")
        f.write(f"Active Stage: {item['active_stage']}\n")
        f.write(f"RAG Status: {item['rag_status']}\n")
        f.write(f"RAG Answer: {item['rag_answer']}\n")
        f.write(f"RAG Metadata: {item['rag_metadata']}\n")
        f.write(f"Stage Pitch: {item['stage_pitch']}\n")
        f.write(f"Next Question: {item['next_question']}\n")
        f.write(f"Suggested Question: {item['suggested_question']}\n")
        f.write(f"Stage Completed: {item['stage_completed']}\n")
        f.write(f"Checklist: {item['checklist']}\n")
        f.write(f"LLM Usage: {item['llm_usage']}\n")
        f.write("\n")

print("\nSaved successfully:")
print("1. live_assist_output.json")
print("2. live_assist_output.txt")
