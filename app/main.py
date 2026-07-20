"""PTO Agent — FastAPI application entry point."""

from pathlib import Path

from fastapi import FastAPI, Header
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .data_store import _EMPLOYEES
from .agent_graph import graph


app = FastAPI(title="PTO Agent")


class ChatRequest(BaseModel):
    message: str


@app.get("/api/users")
def users():
    """Return the employees available in the user switcher."""
    return list(_EMPLOYEES.values())


@app.post("/api/chat")
def chat(
    req: ChatRequest,
    x_user_id: str = Header(default="", alias="X-User-Id"),
):
    """Send the user's message to the PTO Agent LangGraph."""

    emp = _EMPLOYEES.get(x_user_id)

    if not emp:
        return {
            "reply": "I could not identify the authenticated employee."
        }

    print("Authenticated employee:", emp["id"])

    result = graph.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": req.message,
                }
            ],
            "employee_id": emp["id"],
        }
    )

    final_message = result["messages"][-1]

    return {
        "reply": final_message.content
    }


@app.get("/")
def index():
    return FileResponse(
        Path(__file__).parent / "index.html"
    )