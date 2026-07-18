"""TimeOffBot — the app SHELL.

This is your starting point. The chat works: a message you type goes to an
LLM and comes back as plain conversation, and you can switch which employee
you're acting as. That's all it does.

It cannot yet answer policy questions, check leave balances, or submit
time-off requests. Building those capabilities is the lab — see coursework.md.
"""

from ast import arguments
from email.mime import message
import json
from pathlib import Path
from unittest import result

from .tool_schema import TOOLS
from .tools import (search_policy,check_balance,list_leave_requests,submit_leave_request)

from fastapi import FastAPI, Header
from fastapi.responses import FileResponse

from openai import AzureOpenAI
from pydantic import BaseModel

from . import config
from .data_store import _EMPLOYEES

app = FastAPI(title="TimeOffBot")
#Creates the web server

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
        f"You are talking to {emp['full_name']} , based in {emp['country']}."
        if emp
        else "You are talking to an Acme Corp employee."
    )

    system = (
    "You are TimeOffBot, a friendly assistant for Acme Corp employees. "
    + who +
    " You can answer leave policy questions, check leave balances, "
    "and list employee leave requests using the available tools. "
    "Always answer using the authenticated employee's information. "
    "When answering policy questions, use the policy applicable to the employee's country. "
    "If the user asks about another country's policy, explain that your answers are based on their employment country unless they explicitly ask for a comparison."
)
    
    resp = _client().chat.completions.create(
        model=config.AZURE_CHAT_DEPLOYMENT,
        temperature=0.5,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": req.message},
        ],
        tools=TOOLS
    )
    
    message = resp.choices[0].message

    tool_map = {
    "search_policy": search_policy,
    "check_balance": check_balance,
    "list_leave_requests": list_leave_requests,
    "submit_leave_request": submit_leave_request
    }

    if message.tool_calls:

        for tool_call in message.tool_calls:

            function_name = tool_call.function.name
            tool = tool_map[function_name]

            arguments = json.loads(tool_call.function.arguments)

            arguments["employee_id"] = x_user_id
    
            print("Calling:", function_name)

            try:
                result = tool(**arguments)

            except ValueError as e:
                result = {
                    "error": str(e)
                }

            
            messages = [
                 {"role": "system", "content": system},
                 {"role": "user", "content": req.message},
                 message,
            ]

            messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result),
            }
            )

            final_response = _client().chat.completions.create(
                    model=config.AZURE_CHAT_DEPLOYMENT,
                    temperature=0.5,
                    messages=messages,
            )

            return {
                    "reply": final_response.choices[0].message.content
            }

    else:
        return {"reply": message.content}


@app.get("/")
def index():
    return FileResponse(Path(__file__).parent / "index.html")