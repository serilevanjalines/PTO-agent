"""TimeOffBot — the app SHELL.

This is your starting point. The chat works: a message you type goes to an
LLM and comes back as plain conversation, and you can switch which employee
you're acting as. That's all it does.

It cannot yet answer policy questions, check leave balances, or submit
time-off requests. Building those capabilities is the lab — see coursework.md.
"""

import json
from pathlib import Path

from fastapi import FastAPI, Header
from fastapi.responses import FileResponse
from openai import AzureOpenAI
from pydantic import BaseModel

from . import config

app = FastAPI(title="TimeOffBot")
#Creates the web server

employees = json.loads(
    (config.DATA_DIR / "employees.json").read_text()
)

_EMPLOYEES = {}

for e in employees:
    key = e["id"]
    value = e
    _EMPLOYEES[key] = value

class ChatRequest(BaseModel):
    message: str


def _client() -> AzureOpenAI:
    if not (config.AZURE_ENDPOINT and config.AZURE_API_KEY):
        raise RuntimeError(
            "Azure OpenAI credentials are missing. Copy .env.example to .env "
            "and fill in your values."
        )
    return AzureOpenAI(
        azure_endpoint=config.AZURE_ENDPOINT,
        api_key=config.AZURE_API_KEY,
        api_version=config.AZURE_API_VERSION,
    )


@app.get("/api/users")
def users():
    """The employees you can act as, shown in the UI's user switcher."""
    return list(_EMPLOYEES.values())


@app.post("/api/chat")
def chat(req: ChatRequest, x_user_id: str = Header(default="", alias="X-User-Id")):
    """Plain conversation with the LLM — no policy, balance, or request logic yet."""
    emp = _EMPLOYEES.get(x_user_id)
    who = (
        f"You are talking to {emp['full_name']}, based in {emp['country']}."
        if emp
        else "You are talking to an Acme Corp employee."
    )
    system = (
        "You are TimeOffBot, a friendly assistant for Acme Corp employees. "
        + who
        + " Right now you can only make small talk. You cannot look up leave "
        "policies, check balances, or submit time-off requests yet. If the user "
        "asks for any of those, say plainly that you can't do that yet."
    )
    resp = _client().chat.completions.create(
        model=config.AZURE_CHAT_DEPLOYMENT,
        temperature=0.5,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": req.message},
        ],
    )
    return {"reply": resp.choices[0].message.content}


@app.get("/")
def index():
    return FileResponse(Path(__file__).parent / "index.html")