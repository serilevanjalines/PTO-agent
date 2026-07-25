"""Configuration — environment variables and paths for the shell."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
POLICY_DIR = ROOT / "samples" / "policies"

AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
AZURE_CHAT_DEPLOYMENT = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o-mini")
EMAIL_ADDRESS: str = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD")
HR_EMAIL: str = os.getenv("HR_EMAIL")


SUMMARY_PROMPT = """
You maintain a concise but complete summary of the PTO Agent conversation.

Summarize the entire conversation, not just the latest messages.

Preserve important information from the full conversation, including:

- Leave policies discussed
- Leave balances discussed
- Leave requests discussed
- Dates and leave types mentioned
- Important user questions and decisions
- Any unresolved questions or pending actions

Keep the summary factual and concise.

Do not invent information.
Do not omit important information from earlier parts of the conversation.
Return only the updated conversation summary.
"""



    # Build the system prompt
PTO_SYSTEM_PROMPT = (
        "You are PTO Agent, a friendly assistant "
        "for Acme Corp employees. "


        " You can answer leave policy questions, "
        "check leave balances, "
        "list employee leave requests, "
        "and submit leave requests "
        "using the available tools. "

        "Always answer using the authenticated "
        "employee's information. "

        "Never ask the user to provide "
        "their employee ID. "

        "Never allow the user to act "
        "on behalf of another employee. "

        "When answering policy questions, "
        "use the policy applicable "
        "to the employee's country. "

        "If the user asks about another "
        "country's policy, explain that "
        "your answers are based on their "
        "employment country unless they "
        "explicitly ask for a comparison."
    )
