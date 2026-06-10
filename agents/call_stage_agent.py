import json
import os
from groq import Groq
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# client = Groq(api_key=os.getenv("GROQ_API_KEY"))

API_KEY="llmapi_12012d53f7ea92fee92d5888c4cd098a2de420d2a24051afde16257a551c135b"
client = OpenAI(
    api_key=API_KEY,
    base_url="https://api.llmapi.ai/v1"
)
with open(r"D:\Multi_agent\configs\call_stage_config.json", "r") as f:
    STAGES = json.load(f)


STAGE_ORDER = {
    "Introduction": 1,
    "Client Profile": 2,
    "Awareness": 3,
    "Plan Discussion": 4,
    "Cost": 5,
    "Advisory Services": 6,
    "Closing": 7
}

MIN_CONFIDENCE_FOR_TRANSITION = 0.70


def safe_json_parse(text):
    try:
        start = text.find("{")
        end = text.rfind("}") + 1

        if start == -1 or end == 0:
            raise ValueError("No JSON object found")

        return json.loads(text[start:end])

    except Exception:
        return {
            "stage": "Unknown",
            "confidence": 0.0,
            "stage_scores": {},
            "reason": "Could not parse LLM response",
            "evidence": []
        }


def detect_jump_type(previous_stage, current_stage):
    if not previous_stage:
        return "none"

    if previous_stage not in STAGE_ORDER or current_stage not in STAGE_ORDER:
        return "none"

    previous_position = STAGE_ORDER[previous_stage]
    current_position = STAGE_ORDER[current_stage]

    if current_position > previous_position:
        return "forward"
    elif current_position < previous_position:
        return "backward"
    else:
        return "same"


def is_large_jump(previous_stage, current_stage):
    if not previous_stage:
        return False

    if previous_stage not in STAGE_ORDER or current_stage not in STAGE_ORDER:
        return False

    jump_size = abs(STAGE_ORDER[current_stage] - STAGE_ORDER[previous_stage])
    return jump_size > 1


def update_conversation_window(conversation_window, speaker, text, stage=None, max_turns=5):
    if conversation_window is None:
        conversation_window = []

    conversation_window.append({
        "speaker": speaker,
        "stage": stage,
        "text": text
    })

    return conversation_window[-max_turns:]


def detect_stage(transcript, previous_stage=None, conversation_window=None):
    if conversation_window is None:
        conversation_window = []

    stage_names = list(STAGES.keys())

    prompt = f"""
You are a Finideas sales call stage classifier.

Stages:
{json.dumps(STAGES, indent=2)}

Stage order:
{json.dumps(STAGE_ORDER, indent=2)}

Previous stage:
{previous_stage}

Recent conversation context - last 5 turns:
{json.dumps(conversation_window, indent=2)}

Task:
Classify the CURRENT transcript into ONE most likely stage.

Important:
- Use the recent conversation context to understand short or unclear messages.
- But classify mainly based on the current transcript.
- Do not jump stages unless the transcript clearly supports it.
- If current transcript is ambiguous, use previous_stage and recent context.

Rules:
1. Return JSON only.
2. stage must be only one of these:
{stage_names}
3. confidence must be the score of selected stage.
4. stage_scores must contain all stages.
5. Scores should reflect how strongly the transcript belongs to each stage.
6. evidence must contain exact short phrases from current transcript or recent context.
7. Do not add extra text outside JSON.

Return format:
{{
  "stage": "Client Profile",
  "confidence": 0.92,
  "stage_scores": {{
    "Introduction": 0.05,
    "Client Profile": 0.92,
    "Awareness": 0.10,
    "Plan Discussion": 0.15,
    "Cost": 0.02,
    "Advisory Services": 0.01,
    "Closing": 0.01
  }},
  "reason": "Customer is discussing portfolio and investment amount",
  "evidence": [
    "50 lakh portfolio",
    "invest 20 lakh"
  ]
}}

Current transcript:
{transcript}
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
        "agent": "call_stage_agent",
        "llm_calls": 1,
        "prompt_tokens": usage.prompt_tokens if usage else 0,
        "completion_tokens": usage.completion_tokens if usage else 0,
        "total_tokens": usage.total_tokens if usage else 0
    }

    current_stage = result.get("stage", "Unknown")
    confidence = float(result.get("confidence", 0.0))

    stage_changed = False

    if previous_stage and current_stage != previous_stage:
        stage_changed = True

    jump_type = detect_jump_type(previous_stage, current_stage)
    large_jump = is_large_jump(previous_stage, current_stage)

    transition_allowed = True

    if stage_changed and confidence < MIN_CONFIDENCE_FOR_TRANSITION:
        transition_allowed = False

    if jump_type == "backward" and confidence < 0.85:
        transition_allowed = False

    if large_jump and confidence < 0.85:
        transition_allowed = False

    result["previous_stage"] = previous_stage
    result["stage_changed"] = stage_changed
    result["from_stage"] = previous_stage
    result["to_stage"] = current_stage if stage_changed else None
    result["jump_type"] = jump_type
    result["large_jump"] = large_jump
    result["transition_allowed"] = transition_allowed
    result["conversation_window_size"] = len(conversation_window)

    return result


if __name__ == "__main__":

    previous_stage = None
    conversation_window = []

    examples = [
        {
            "speaker": "advisor",
            "text": "Hello sir, I am calling from Finideas."
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
            "text": "I can invest around 25 lakh initially."
        },
        {
            "speaker": "customer",
            "text": "What is NIFTY ETF and how hedging works?"
        },
        {
            "speaker": "advisor",
            "text": "Let me explain the Relax Plan and Basic Plan."
        },
        {
            "speaker": "customer",
            "text": "What are your advisory charges and brokerage?"
        },
        {
            "speaker": "customer",
            "text": "Okay, what is the next step for KYC?"
        }
    ]

    for item in examples:
        transcript = item["text"]
        speaker = item["speaker"]

        print("=" * 70)
        print("Speaker:", speaker)
        print("Transcript:", transcript)

        result = detect_stage(
            transcript=transcript,
            previous_stage=previous_stage,
            conversation_window=conversation_window
        )

        print(json.dumps(result, indent=2))

        if result["transition_allowed"]:
            previous_stage = result["stage"]
        else:
            print("Stage transition blocked due to low confidence or suspicious jump.")

        conversation_window = update_conversation_window(
            conversation_window=conversation_window,
            speaker=speaker,
            text=transcript,
            stage=previous_stage,
            max_turns=5
        )

        print("\nLast 5 conversation turns:")
        print(json.dumps(conversation_window, indent=2))