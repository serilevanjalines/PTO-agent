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
)

from langgraph.graph import (
    MessagesState,
    StateGraph,
    START,
    END,
)


# ============================================================
# 1. GRAPH STATE
# ============================================================

class State(MessagesState):
    employee_id: str


# Create the graph builder
builder = StateGraph(State)


# ============================================================
# 2. AGENT NODE
# ============================================================

def agent_node(state: State):

    messages = state["messages"]
    employee_id = state["employee_id"]

    print("Agent running for:", employee_id)

    # --------------------------------------------------------
    # System prompt
    # --------------------------------------------------------

    system_message = {
        "role": "system",
        "content": (
            "You are TimeOffBot, a friendly assistant for Acme Corp employees. "
            f"The authenticated employee ID is {employee_id}. "
            "Always use this authenticated employee ID when calling tools. "
            "Never ask the user to provide their employee ID."
        ),
    }

    # --------------------------------------------------------
    # Convert LangGraph messages
    # into Azure OpenAI message format
    # --------------------------------------------------------

    openai_messages = [
        system_message
    ]

    for message in messages:

        # ----------------------------------------------------
        # HumanMessage
        # ----------------------------------------------------

        if isinstance(message, HumanMessage):

            openai_messages.append(
                {
                    "role": "user",
                    "content": message.content,
                }
            )

        # ----------------------------------------------------
        # AIMessage
        # ----------------------------------------------------

        elif isinstance(message, AIMessage):

            assistant_message = {
                "role": "assistant",
                "content": message.content or "",
            }

            # AIMessage may contain tool calls
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
        # ToolMessage
        # ----------------------------------------------------

        elif isinstance(message, ToolMessage):

            openai_messages.append(
                {
                    "role": "tool",
                    "tool_call_id": message.tool_call_id,
                    "content": message.content,
                }
            )

    # --------------------------------------------------------
    # Call Azure OpenAI
    # --------------------------------------------------------

    response = _client().chat.completions.create(
        model=config.AZURE_CHAT_DEPLOYMENT,
        temperature=0.5,
        messages=openai_messages,
        tools=TOOLS,
    )

    message = response.choices[0].message

    # --------------------------------------------------------
    # Convert Azure response into LangGraph AIMessage
    # --------------------------------------------------------

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

    # The last message should be an AIMessage here.
    # Only AIMessage can contain tool calls.

    if isinstance(last_message, AIMessage):

        if last_message.tool_calls:

            return "tools"

    # No tool call means the LLM has produced
    # its final response.

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

    # --------------------------------------------------------
    # Execute every tool requested by the LLM
    # --------------------------------------------------------

    for tool_call in last_message.tool_calls:

        function_name = tool_call["name"]

        tool = tool_map[function_name]

        arguments = tool_call["args"]

        # ----------------------------------------------------
        # IMPORTANT SECURITY RULE
        #
        # Never trust employee_id from the LLM.
        #
        # Always inject the authenticated employee ID.
        # ----------------------------------------------------

        arguments["employee_id"] = state["employee_id"]

        print(
            "Calling:",
            function_name
        )

        # ----------------------------------------------------
        # Execute tool
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
        # Convert result into LangGraph ToolMessage
        # ----------------------------------------------------

        tool_messages.append(
            ToolMessage(
                content=json.dumps(
                    result
                ),
                tool_call_id=tool_call["id"],
            )
        )

    # --------------------------------------------------------
    # Return all tool results to graph state
    # --------------------------------------------------------

    return {
        "messages": tool_messages
    }


# ============================================================
# 5. BUILD GRAPH
# ============================================================

# Register nodes

builder.add_node(
    "agent",
    agent_node
)

builder.add_node(
    "tools",
    tool_node
)


# ============================================================
# 6. GRAPH FLOW
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
# 8. TEST GRAPH
# ============================================================

if __name__ == "__main__":

    result = graph.invoke(
        {
            "messages": [
                HumanMessage(
                    content="Check my annual leave balance."
                )
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