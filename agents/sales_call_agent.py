import json
import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from agents.call_stage_agent import detect_stage, update_conversation_window
from agents.checklist_agent import checklist_agent


STAGE_ORDER_LIST = [
    "Introduction",
    "Client Profile",
    "Awareness",
    "Plan Discussion",
    "Cost",
    "Advisory Services",
    "Closing"
]


NEXT_STAGE_QUESTIONS = {
    "Introduction": "Can I quickly explain who we are, Finideas, and the purpose of this call?",
    "Client Profile": "Can you tell me about your stock market experience, portfolio size, and investment horizon?",
    "Awareness": "Are you aware of NIFTY, ETF, hedging, and downside protection?",
    "Plan Discussion": "Which plan would you like to discuss: Relax, Basic, Comfort, Power Booster, Marathon, Dynamic, or Finrakshak?",
    "Cost": "Would you like me to explain advisory cost, brokerage, tax, and total charges?",
    "Advisory Services": "Do you need help with research support, broker connection, or API integration?",
    "Closing": "Shall we move ahead with KYC, app download, or a follow-up meeting?"
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

            next_best_question = NEXT_STAGE_QUESTIONS.get(
                next_stage,
                checklist_result.get("next_best_question", "")
            )
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

    return {
        "stage_detection": stage_result,
        "active_stage": active_stage,
        "stage_completed": stage_completed,
        "checklist": checklist_result,
        "checklist_status_by_stage": checklist_status_by_stage,
        "next_best_question": next_best_question,
        "conversation_window": updated_conversation_window
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
            "speaker": "advisor",
            "text": "You are interested in our Fin Raster strategy, where we provide hedging solutions for existing mutual fund and equity portfolios. Is this a good time to discuss?"
        },
        {
            "speaker": "customer",
            "text": "Yes. I saw some YouTube videos and wanted to know the minimum amount needed for investment."
        },
        {
            "speaker": "advisor",
            "text": "We run two kinds of models. In the advisory model, we create a new portfolio using Nifty ETF and Nifty futures, and hedge it with December put options of the Nifty."
        },
        {
            "speaker": "advisor",
            "text": "The minimum investment is one lot of Nifty, which comes to around 16 lakh rupees at present."
        },
        {
            "speaker": "customer",
            "text": "Okay."
        },
        {
            "speaker": "advisor",
            "text": "Out of the 16 lakh, around 10 percent, that is 1.6 lakh, is used for futures and options for the full year."
        },
        {
            "speaker": "advisor",
            "text": "Using this 1.6 lakh, we create a position equivalent to 16 lakh in Nifty, which is downside protected."
        },
        {
            "speaker": "advisor",
            "text": "To recover this cost, the remaining funds are parked in fixed income instruments ranging from 7.5% to 14-15%. You get around 9-10% back from there."
        },
        {
            "speaker": "advisor",
            "text": "The maximum risk in this scenario is less than 2%. Even if the market goes down by 50%, you are not expected to lose more than 2% on the entire 16 lakh investment."
        },
        {
            "speaker": "customer",
            "text": "So 16 lakh is the minimum amount needed for an investor, right?"
        },
        {
            "speaker": "advisor",
            "text": "Yes. If you can create a 16 lakh position using just 10 percent funds, you may manage the remaining 90 percent yourself, but only if you can generate more than 9 percent annual returns."
        },
        {
            "speaker": "advisor",
            "text": "If you are not sure about generating that return yourself, it is better to invest the full 16 lakh and protect the downside."
        },
        {
            "speaker": "customer",
            "text": "You said from 16 lakh, 10 percent goes into futures and options, right?"
        },
        {
            "speaker": "advisor",
            "text": "Yes. We buy one lot of futures and one lot of put options for the year."
        },
        {
            "speaker": "customer",
            "text": "And how much do you invest in ETF?"
        },
        {
            "speaker": "advisor",
            "text": "In one lot, we do not buy the Nifty ETF. You can buy Nifty ETF for 4-5 lakh also, but protection is not available for 4 lakh. Protection is available directly for 16 lakh."
        },
        {
            "speaker": "advisor",
            "text": "The objective of creating one lot, or 16 lakh exposure, is met using Nifty futures. One lot of Nifty futures gives equivalent market exposure."
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
            f.write("\n\n")

            print(f"Processed example {idx}/{len(examples)}")

    print("\nOutput saved to sales_call_trace.txt")