import sys
import os
import json

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from agents.checklist_agent import checklist_agent


stage = "Client Profile"

current_status = {
    "client_experience": [],
    "awareness": [],
    "existing_portfolio": [],
    "preferred_plan": [],
    "investment_amount": [],
    "swp_requirement": [],
    "investment_horizon": [],
    "debt_preference": []
}

examples = [
    "I have been investing in stocks for the last 8 years.",
    "Yes, I attended your webinar and watched the product videos.",
    "I currently have a portfolio of around 2 crore rupees.",
    "I am more interested in the Finrakshak plan.",
    # "I can invest around 25 lakh initially.",
    # "I would like monthly withdrawals from my investment.",
    # "My investment horizon is around 10 years.",
    # "I prefer Bharat Bond and Gold as debt investments."
]

for text in examples:
    print("=" * 60)
    print("Transcript:", text)

    result = checklist_agent(stage, text, current_status)

    current_status = result["final_status"]

    print("\nAgent Result:")
    print(json.dumps(result, indent=2))

    print("\nCurrent Checklist Status:")
    print(json.dumps(current_status, indent=2))