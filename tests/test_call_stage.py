import json
import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from agents.call_stage_agent import detect_stage

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