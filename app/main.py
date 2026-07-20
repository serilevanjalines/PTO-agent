"""PTO Agent — FastAPI application entry point."""

from pathlib import Path

from fastapi import FastAPI, Header
from fastapi.responses import FileResponse
from pydantic import BaseModel
#to convert json into python objects

from .data_store import _EMPLOYEES
from .agent_graph import graph


app = FastAPI(title="PTO Agent")


class ChatRequest(BaseModel):
    message: str


@app.get("/api/users")
def users():
    """Return the employees available in the user switcher."""

    return list(
        _EMPLOYEES.values()
    )



@app.post("/api/chat")
def chat(
    req: ChatRequest,
    x_user_id: str = Header(
        default="",
        alias="X-User-Id",
    ),
):
    """Send the user's message to the PTO Agent LangGraph."""


    emp = _EMPLOYEES.get(
        x_user_id
    )

    if not emp:

        return {
            "reply": (
                "I could not identify "
                "the authenticated employee."
            )
        }

    print(
        "Authenticated employee:",
        emp["id"]
    )



    who = (
        f"You are talking to {emp['full_name']} "
        f"whose id is {emp['id']}, "
        f"based in {emp['country']}."
    )



    system = (
        "You are PTO Agent, a friendly assistant "
        "for Acme Corp employees. "

        + who +

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



    result = graph.invoke(
        {
            "messages": [
                {
                    "role": "system",
                    "content": system,
                },
                {
                    "role": "user",
                    "content": req.message,
                },
            ],

            "employee_id": emp["id"],
        }
    )



    final_message = result["messages"][-1]


    return {
        "reply": final_message.content
    }


# ============================================================
# SERVE FRONTEND
# ============================================================

@app.get("/")
def index():

    return FileResponse(
        Path(__file__).parent / "index.html"
    )