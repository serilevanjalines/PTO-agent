import json

from . import config
from .llm_client import _client
from .tool_schema import TOOLS

from .tools import (
    search_policy,
    check_balance,
    list_leave_requests,
    submit_leave_request,
)

from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    ToolMessage,
    SystemMessage,
)

from langgraph.graph import (
    MessagesState,
    StateGraph,
    START,
    END,
)


class State(MessagesState):
    employee_id: str


# ============================================================
# 1. CREATE GRAPH BUILDER
# ============================================================

builder = StateGraph(State)


# ============================================================
# 2. AGENT NODE
# ============================================================

def agent_node(state: State):

    messages = state["messages"]
    employee_id = state["employee_id"]

    print("Agent running for:", employee_id)

    # Convert LangGraph/LangChain messages
    # into the dictionary format expected by Azure OpenAI.
    openai_messages = []

    for message in messages:

        # ----------------------------------------------------
        # System message
        # ----------------------------------------------------

        if isinstance(message, SystemMessage):

            openai_messages.append(
                {
                    "role": "system",
                    "content": message.content,
                }
            )

        # ----------------------------------------------------
        # Human message
        # ----------------------------------------------------

        elif isinstance(message, HumanMessage):

            openai_messages.append(
                {
                    "role": "user",
                    "content": message.content,
                }
            )

        # ----------------------------------------------------
        # AI message
        # ----------------------------------------------------

        elif isinstance(message, AIMessage):

            assistant_message = {
                "role": "assistant",
                "content": message.content or "",
            }

            # AIMessage may contain tool calls.
            if message.tool_calls:

                assistant_message["tool_calls"] = [
                    {
                        "id": tool_call["id"],
                        "type": "function",
                        "function": {
                            "name": tool_call["name"],
                            "arguments": json.dumps(
                                tool_call["args"]
                            ),
                        },
                    }
                    for tool_call in message.tool_calls
                ]

            openai_messages.append(
                assistant_message
            )

        # ----------------------------------------------------
        # Tool message
        # ----------------------------------------------------

        elif isinstance(message, ToolMessage):

            openai_messages.append(
                {
                    "role": "tool",
                    "tool_call_id": message.tool_call_id,
                    "content": message.content,
                }
            )

    # ========================================================
    # CALL AZURE OPENAI
    # ========================================================

    response = _client().chat.completions.create(
        model=config.AZURE_CHAT_DEPLOYMENT,
        temperature=0.5,
        messages=openai_messages,
        tools=TOOLS,
    )

    message = response.choices[0].message

    # ========================================================
    # CONVERT AZURE RESPONSE INTO LANGGRAPH AIMessage
    # ========================================================

    tool_calls = []

    if message.tool_calls:

        for tool_call in message.tool_calls:

            tool_calls.append(
                {
                    "name": tool_call.function.name,
                    "args": json.loads(
                        tool_call.function.arguments
                    ),
                    "id": tool_call.id,
                }
            )

    assistant_message = AIMessage(
        content=message.content or "",
        tool_calls=tool_calls,
    )

    return {
        "messages": [
            assistant_message
        ]
    }


# ============================================================
# 3. DECISION NODE
# ============================================================

def should_continue(state: State):

    last_message = state["messages"][-1]

    # Only an AIMessage can request tools.
    if isinstance(last_message, AIMessage):

        if last_message.tool_calls:

            return "tools"

    # No tool calls means the LLM has
    # produced the final answer.
    return END


# ============================================================
# 4. TOOL NODE
# ============================================================

def tool_node(state: State):

    last_message = state["messages"][-1]

    tool_map = {

        "search_policy":
            search_policy,

        "check_balance":
            check_balance,

        "list_leave_requests":
            list_leave_requests,

        "submit_leave_request":
            submit_leave_request,

    }

    tool_messages = []

    # ========================================================
    # EXECUTE EVERY TOOL REQUESTED BY THE LLM
    # ========================================================

    for tool_call in last_message.tool_calls:

        function_name = tool_call["name"]

        tool = tool_map[function_name]

        arguments = tool_call["args"]

        # ----------------------------------------------------
        # SECURITY RULE
        #
        # Never trust employee_id provided by the LLM.
        # Always use the authenticated employee ID.
        # ----------------------------------------------------

        arguments["employee_id"] = state["employee_id"]

        print(
            "Calling:",
            function_name
        )

        # ----------------------------------------------------
        # EXECUTE TOOL
        # ----------------------------------------------------

        try:

            result = tool(
                **arguments
            )

        except ValueError as e:

            result = {
                "error": str(e)
            }

        except Exception as e:

            result = {
                "error": str(e)
            }

        # ----------------------------------------------------
        # CONVERT RESULT INTO LANGGRAPH ToolMessage
        # ----------------------------------------------------

        tool_messages.append(
            ToolMessage(
                content=json.dumps(
                    result
                ),
                tool_call_id=tool_call["id"],
            )
        )

    # Return all tool results to graph state.
    return {
        "messages": tool_messages
    }


# ============================================================
# 5. REGISTER NODES
# ============================================================

builder.add_node(
    "agent",
    agent_node
)

builder.add_node(
    "tools",
    tool_node
)


# ============================================================
# 6. DEFINE GRAPH FLOW
# ============================================================

# START → Agent

builder.add_edge(
    START,
    "agent"
)


# Agent → Tools OR END

builder.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        END: END,
    }
)


# Tools → Agent

builder.add_edge(
    "tools",
    "agent"
)


# ============================================================
# 7. COMPILE GRAPH
# ============================================================

graph = builder.compile()


# ============================================================
# 8. TEST GRAPH DIRECTLY
# ============================================================

if __name__ == "__main__":

    result = graph.invoke(
        {
            "messages": [
                SystemMessage(
                    content=(
                        "You are PTO Agent, a friendly assistant "
                        "for Acme Corp employees. "
                        "The authenticated employee ID is E001. "
                        "Never ask the user to provide their "
                        "employee ID."
                    )
                ),
                HumanMessage(
                    content="Check my annual leave balance."
                ),
            ],
            "employee_id": "E001",
        }
    )

    print(
        "\n\n===== FINAL GRAPH STATE =====\n"
    )

    for message in result["messages"]:

        print(
            "TYPE:",
            type(message).__name__
        )

        print(
            "CONTENT:",
            message.content
        )

        if isinstance(
            message,
            AIMessage
        ):

            print(
                "TOOL CALLS:",
                message.tool_calls
            )

        print(
            "-" * 50
        )