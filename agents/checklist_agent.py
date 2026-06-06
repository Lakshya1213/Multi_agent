import json
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

with open(r"D:\Multi_agent\configs\checklist_config.json", "r") as f:
    CHECKLISTS = json.load(f)


def safe_json_parse(text):
    try:
        start = text.find("{")
        end = text.rfind("}") + 1

        if start == -1 or end == 0:
            raise ValueError("No JSON object found")

        return json.loads(text[start:end])

    except Exception:
        return {
            "stage": "",
            "updated_status": {},
            "covered_items": [],
            "missing_items": [],
            "next_best_question": "",
            "reason": "Could not parse LLM response"
        }


def normalize_status(stage_checklist, current_status):
    status = {}

    for item in stage_checklist.keys():
        value = current_status.get(item, [])

        if isinstance(value, list):
            status[item] = value
        elif value:
            status[item] = [value]
        else:
            status[item] = []

    return status


def calculate_progress(status):
    total = len(status)

    if total == 0:
        return 0.0

    covered = sum(1 for value in status.values() if len(value) > 0)

    return round(covered / total, 2)


def checklist_agent(stage, transcript, current_status=None):
    if current_status is None:
        current_status = {}

    stage_checklist = CHECKLISTS.get(stage, {})
    normalized_status = normalize_status(stage_checklist, current_status)

    prompt = f"""
You are a Finideas Checklist Agent.

Your job:
1. Read the transcript.
2. Check which checklist items are covered.
3. Extract actual values from the transcript.
4. Update checklist status.
5. Find missing items.
6. Suggest ONE next best question for seller.

Important rules:
1. Return JSON only.
2. updated_status must store actual extracted text/value, not true/false.
3. Use exact checklist item names only.
4. Do not remove old values from current checklist status.
5. If nothing is found for an item, do not include that item in updated_status.
6. covered_items means items that have at least one value after update.
7. missing_items means items that still have empty list after update.
8. next_best_question should ask only about the most important missing item.
9. Do not repeat questions whose values are already present in current checklist status.

Example:
If transcript says: "I can invest around 25 lakh initially"
Return:
"updated_status": {{
  "investment_amount": ["25 lakh initially"]
}}

Stage:
{stage}

Checklist for this stage:
{json.dumps(stage_checklist, indent=2)}

Current checklist status:
{json.dumps(normalized_status, indent=2)}

Transcript:
{transcript}

Return JSON only in this format:
{{
  "stage": "{stage}",
  "updated_status": {{
    "item_name": ["actual value found in transcript"]
  }},
  "covered_items": [],
  "missing_items": [],
  "next_best_question": "",
  "reason": ""
}}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        temperature=0,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    result = safe_json_parse(response.choices[0].message.content)

    updated_status = result.get("updated_status", {})
    final_status = normalized_status.copy()

    for item, values in updated_status.items():
        if item not in final_status:
            continue

        if not isinstance(values, list):
            values = [values]

        for value in values:
            if value and value not in final_status[item]:
                final_status[item].append(value)

    covered_items = [
        item for item, values in final_status.items()
        if len(values) > 0
    ]

    missing_items = [
        item for item, values in final_status.items()
        if len(values) == 0
    ]

    completion_score = calculate_progress(final_status)

    result["stage"] = stage
    result["final_status"] = final_status
    result["covered_items"] = covered_items
    result["missing_items"] = missing_items
    result["completion_score"] = completion_score
    result["completion_percent"] = round(completion_score * 100, 2)

    return result


if __name__ == "__main__":
    stage = "Client Profile"

    current_status = {
        "client_experience": [],
        "webinar_awareness": [],
        "existing_portfolio": [],
        "preferred_plan": [],
        "investment_amount": [],
        "investment_type": [],
        "swp_requirement": [],
        "investment_horizon": [],
        "debt_preference": [],
        "existing_broker": []
    }

    examples = [
        "I have been investing in stocks for the last 8 years.",
        "I attended your webinar yesterday.",
        "I have around 50 lakh portfolio.",
        "I can invest around 20 lakh.",
        "I want monthly withdrawal also.",
        "My horizon is around 10 years."
    ]

    for transcript in examples:
        print("=" * 70)
        print("Transcript:", transcript)

        result = checklist_agent(
            stage=stage,
            transcript=transcript,
            current_status=current_status
        )

        print(json.dumps(result, indent=2))

        current_status = result["final_status"]