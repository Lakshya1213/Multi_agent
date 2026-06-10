import json
import sys
import os

from openai import OpenAI
from dotenv import load_dotenv

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from agents.call_stage_agent import detect_stage, update_conversation_window
from agents.checklist_agent import checklist_agent

API_KEY="llmapi_12012d53f7ea92fee92d5888c4cd098a2de420d2a24051afde16257a551c135b"

load_dotenv()

client = OpenAI(
    api_key=API_KEY,
    base_url="https://api.llmapi.ai/v1"
)


STAGE_ORDER_LIST = [
    "Introduction",
    "Client Profile",
    "Awareness",
    "Plan Discussion",
    "Cost",
    "Advisory Services",
    "Closing"
]


def safe_json_parse(text):
    try:
        start = text.find("{")
        end = text.rfind("}") + 1

        if start == -1 or end == 0:
            raise ValueError("No JSON object found")

        return json.loads(text[start:end])

    except Exception:
        return {
            "pitch": "",
            "objective": "",
            "covered_items_summary": "",
            "focus_items": [],
            "next_question": "",
            "reason": "Could not parse LLM pitch response"
        }


def generate_stage_pitch(previous_stage, current_stage, transcript, checklist_result):
    covered_items = checklist_result.get("covered_items", [])
    missing_items = checklist_result.get("missing_items", [])
    completion_percent = checklist_result.get("completion_percent", 0)

    prompt = f"""
You are a Finideas live sales call assistant.

The call stage has changed.

Previous stage:
{previous_stage}

Current stage:
{current_stage}

Current transcript:
{transcript}

Checklist covered items:
{covered_items}

Checklist missing items:
{missing_items}

Checklist completion:
{completion_percent}%

Task:
Generate a short advisor pitch for the NEW current stage.

Rules:
1. Return JSON only.
2. Pitch should tell advisor what to say next.
3. Use missing checklist items as main focus.
4. Keep it practical and short.
5. Do not speak directly to customer. Guide the advisor.

Return format:
{{
  "pitch": "Now shift the conversation to client profiling. First acknowledge the client, then ask about portfolio size, investment amount, and investment horizon.",
  "objective": "Collect important client profile details",
  "covered_items_summary": "Client has already shared stock market experience.",
  "focus_items": ["existing_portfolio", "investment_amount", "investment_horizon"],
  "next_question": "Can you tell me your current portfolio size and how much you are planning to invest?",
  "reason": "Stage changed from Introduction to Client Profile"
}}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    result = safe_json_parse(response.choices[0].message.content)

    usage = response.usage

    result["llm_usage"] = {
        "agent": "stage_pitch_agent",
        "llm_calls": 1,
        "prompt_tokens": usage.prompt_tokens if usage else 0,
        "completion_tokens": usage.completion_tokens if usage else 0,
        "total_tokens": usage.total_tokens if usage else 0
    }

    return result


def generate_stage_assistance(stage, checklist_result):
    missing_items = checklist_result.get("missing_items", [])
    completion_percent = checklist_result.get("completion_percent", 0)

    if completion_percent >= 95:
        return {
            "stage": stage,
            "message": f"{stage} stage is completed. Move to next stage.",
            "remaining_items": []
        }

    return {
        "stage": stage,
        "message": (
            f"You are currently in {stage} stage. "
            f"Remaining checklist items are: {', '.join(missing_items)}."
        ),
        "remaining_items": missing_items
    }


def calculate_total_llm_usage(stage_result, checklist_result, stage_pitch=None):
    stage_usage = stage_result.get("llm_usage", {})
    checklist_usage = checklist_result.get("llm_usage", {})
    pitch_usage = stage_pitch.get("llm_usage", {}) if stage_pitch else {}

    return {
        "total_llm_calls": (
            stage_usage.get("llm_calls", 0)
            + checklist_usage.get("llm_calls", 0)
            + pitch_usage.get("llm_calls", 0)
        ),
        "total_prompt_tokens": (
            stage_usage.get("prompt_tokens", 0)
            + checklist_usage.get("prompt_tokens", 0)
            + pitch_usage.get("prompt_tokens", 0)
        ),
        "total_completion_tokens": (
            stage_usage.get("completion_tokens", 0)
            + checklist_usage.get("completion_tokens", 0)
            + pitch_usage.get("completion_tokens", 0)
        ),
        "total_tokens": (
            stage_usage.get("total_tokens", 0)
            + checklist_usage.get("total_tokens", 0)
            + pitch_usage.get("total_tokens", 0)
        ),
        "by_agent": {
            "call_stage_agent": stage_usage,
            "checklist_agent": checklist_usage,
            "stage_pitch_agent": pitch_usage
        }
    }


def get_next_stage(current_stage):
    if current_stage not in STAGE_ORDER_LIST:
        return current_stage

    index = STAGE_ORDER_LIST.index(current_stage)

    if index + 1 < len(STAGE_ORDER_LIST):
        return STAGE_ORDER_LIST[index + 1]

    return current_stage


def sales_call_agent(
    transcript,
    speaker="customer",
    previous_stage=None,
    checklist_status_by_stage=None,
    conversation_window=None
):
    initial_stage = previous_stage

    if checklist_status_by_stage is None:
        checklist_status_by_stage = {}

    if conversation_window is None:
        conversation_window = []

    stage_result = detect_stage(
        transcript=transcript,
        previous_stage=previous_stage,
        conversation_window=conversation_window
    )

    detected_stage = stage_result["stage"]

    if stage_result["transition_allowed"]:
        active_stage = detected_stage
    else:
        active_stage = previous_stage

    if active_stage is None:
        active_stage = detected_stage

    current_stage_status = checklist_status_by_stage.get(active_stage, {})

    checklist_result = checklist_agent(
        stage=active_stage,
        transcript=transcript,
        current_status=current_stage_status
    )

    checklist_status_by_stage[active_stage] = checklist_result["final_status"]

    completion_percent = checklist_result["completion_percent"]
    stage_completed = completion_percent >= 95.0

    if stage_completed:
        next_stage = get_next_stage(active_stage)

        if next_stage != active_stage:
            active_stage = next_stage
            next_stage_status = checklist_status_by_stage.get(next_stage, {})

            checklist_result = checklist_agent(
                stage=next_stage,
                transcript="",
                current_status=next_stage_status
            )

            checklist_status_by_stage[next_stage] = checklist_result["final_status"]
            next_best_question = checklist_result.get("next_best_question", "")

        else:
            next_best_question = "All stages are completed. Summarize the call and confirm final next steps."

    else:
        next_best_question = checklist_result.get("next_best_question", "")

    updated_conversation_window = update_conversation_window(
        conversation_window=conversation_window,
        speaker=speaker,
        text=transcript,
        stage=active_stage,
        max_turns=5
    )

    stage_assistance = generate_stage_assistance(
        active_stage,
        checklist_result
    )

    stage_pitch = None

    if initial_stage is not None and initial_stage != active_stage:
        stage_pitch = generate_stage_pitch(
            previous_stage=initial_stage,
            current_stage=active_stage,
            transcript=transcript,
            checklist_result=checklist_result
        )

    llm_usage = calculate_total_llm_usage(
        stage_result,
        checklist_result,
        stage_pitch
    )

    return {
        "stage_detection": stage_result,
        "active_stage": active_stage,
        "stage_completed": stage_completed,
        "checklist": checklist_result,
        "stage_assistance": stage_assistance,
        "stage_pitch": stage_pitch,
        "checklist_status_by_stage": checklist_status_by_stage,
        "next_best_question": next_best_question,
        "conversation_window": updated_conversation_window,
        "llm_usage": llm_usage
    }


if __name__ == "__main__":

    previous_stage = None
    conversation_window = []
    checklist_status_by_stage = {}

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

    with open("sales_call_trace.txt", "w", encoding="utf-8") as f:

        for idx, item in enumerate(examples, start=1):

            speaker = item["speaker"]
            transcript = item["text"]

            result = sales_call_agent(
                transcript=transcript,
                speaker=speaker,
                previous_stage=previous_stage,
                checklist_status_by_stage=checklist_status_by_stage,
                conversation_window=conversation_window
            )

            f.write("=" * 70 + "\n")
            f.write(f"EXAMPLE #{idx}\n")
            f.write(f"Speaker: {speaker}\n")
            f.write(f"Transcript: {transcript}\n\n")

            f.write("RESULT:\n")
            f.write(json.dumps(result, indent=2))
            f.write("\n\n")

            previous_stage = result["active_stage"]
            checklist_status_by_stage = result["checklist_status_by_stage"]
            conversation_window = result["conversation_window"]

            f.write(f"Current Stage: {previous_stage}\n")
            f.write(f"Stage Completed: {result['stage_completed']}\n")
            f.write(f"Next Question: {result['next_best_question']}\n")

            if result["stage_pitch"]:
                f.write("Stage Pitch:\n")
                f.write(json.dumps(result["stage_pitch"], indent=2))
                f.write("\n")

            f.write("\n\n")

            print(f"Processed example {idx}/{len(examples)}")

    print("\nOutput saved to sales_call_trace.txt")