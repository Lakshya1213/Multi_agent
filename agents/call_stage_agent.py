import json
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

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


STAGE_QUESTIONS = {
    "Introduction": "Can I quickly explain who we are and how Finideas helps investors?",
    "Client Profile": "Can you tell me your current portfolio size and investment horizon?",
    "Awareness": "Are you already aware of NIFTY, ETF, hedging, and downside protection?",
    "Plan Discussion": "Which plan are you more interested in: Relax, Basic, Marathon, Power Booster, or Finrakshak?",
    "Cost": "Would you like me to explain the advisory fee, brokerage, and tax structure clearly?",
    "Advisory Services": "Do you need help with research support, broker connection, or API integration?",
    "Closing": "Shall we move ahead with the next step like KYC or app download?"
}


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


def detect_stage(transcript, previous_stage=None):
    stage_names = list(STAGES.keys())

    prompt = f"""
You are a Finideas sales call stage classifier.

Stages:
{json.dumps(STAGES, indent=2)}

Stage order:
{json.dumps(STAGE_ORDER, indent=2)}

Task:
Classify the transcript into ONE most likely stage.

Also give confidence score for EACH stage from 0 to 1.

Rules:
1. Return JSON only.
2. stage must be only one of these:
{stage_names}
3. confidence must be the score of selected stage.
4. stage_scores must contain all stages.
5. Scores should reflect how strongly the transcript belongs to each stage.
6. evidence must contain exact short phrases from transcript that support the stage.
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

Transcript:
{transcript}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        temperature=0,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    result = safe_json_parse(response.choices[0].message.content)

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

    result["next_best_question"] = STAGE_QUESTIONS.get(
        current_stage,
        "Can you share a little more so I can guide the conversation better?"
    )

    return result


if __name__ == "__main__":

    previous_stage = None

    examples = [
        "Hello sir, I am calling from Finideas.",
        "I have been investing in stocks for the last 8 years.",
        "Yes, I attended your webinar and watched the product videos.",
        "I currently have a portfolio of around 2 crore rupees.",
        "I am more interested in the Finrakshak plan.",
        "I can invest around 25 lakh initially.",
        "I would like monthly withdrawals from my investment.",
        "My investment horizon is around 10 years.",
        "I prefer Bharat Bond and Gold as debt investments.",
        "What is NIFTY ETF and how hedging works?",
        "Tell me about Relax Plan and Power Booster.",
        "What are your advisory charges and brokerage?",
        "Do you provide research support and broker API integration?",
        "Okay, what is the next step for KYC?"
    ]

    for transcript in examples:
        print("=" * 70)
        print("Transcript:", transcript)

        result = detect_stage(
            transcript=transcript,
            previous_stage=previous_stage
        )

        print(json.dumps(result, indent=2))

        if result["transition_allowed"]:
            previous_stage = result["stage"]
        else:
            print("Stage transition blocked due to low confidence or suspicious jump.")