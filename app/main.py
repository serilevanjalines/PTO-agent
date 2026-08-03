"""PTO Agent — FastAPI application entry point."""

from pathlib import Path

from openai import BadRequestError
import logging


from fastapi import FastAPI, Header
from fastapi.responses import FileResponse
from pydantic import BaseModel
#to convert json into python objects

from .data_store import _EMPLOYEES
from .agent_graph import graph


app = FastAPI(title="PTO Agent")

logger = logging.getLogger(__name__)


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

    
    

    try :
            result = graph.invoke(
            {
                "messages": [
                {
                "role": "user",
                "content": req.message,
            },
        ],
        "employee_id": emp["id"],
    },
    config={
        "configurable": {
            "thread_id": emp["id"],
        }
    }
)

    except ValueError as e:
        return {
        "reply": str(e)
    }

    except BadRequestError:
        return {
        "reply": (
            "I'm sorry, but I couldn't process that request. "
            "Could you rephrase it or provide a little more detail?"
        )
    }

    except Exception:
        logger.exception("Unexpected error while invoking PTO Agent.")

        return {
        "reply": (
            "Sorry, something went wrong while processing your request. "
            "Please try again."
        )
    }



    final_message = result["messages"][-1]


    return {
        "reply": final_message.content
    }




@app.get("/")
def index():

    return FileResponse(
        Path(__file__).parent / "index.html"
    )