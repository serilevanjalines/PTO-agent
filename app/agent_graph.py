import json

from . import config
from .llm_client import _client
from .tool_schema import TOOLS
from langgraph.checkpoint.memory import MemorySaver
from .data_store import _EMPLOYEES


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
    RemoveMessage,
)

from langgraph.graph import (
    MessagesState,
    StateGraph,
    START,
    END,
)




class State(MessagesState):
    employee_id: str
    conversation_summary: str = ""



builder = StateGraph(State)



def trim_messages(messages, max_messages=10):
    # Always keep the system message
    system_messages = [
        message
        for message in messages
        if isinstance(message, SystemMessage)
    ]

    # Everything except system messages
    conversation = [
        message
        for message in messages
        if not isinstance(message, SystemMessage)
    ]

    # Take the most recent messages
    recent_messages = conversation[-max_messages:]

    # If trimming starts with a ToolMessage,
    # remove it because its AI tool-call was trimmed away.
    while recent_messages and isinstance(
        recent_messages[0],
        ToolMessage
    ):
        recent_messages.pop(0)

    return system_messages + recent_messages





def summarize_node(state: State):

    messages = state["messages"]

    old_summary = state.get(
        "conversation_summary",
        ""
    )

    summary_messages = [
        {
            "role": "system",
            "content": config.SUMMARY_PROMPT,
        }
    ]

    # Include the previous summary if one exists
    if old_summary:

        summary_messages.append(
            {
                "role": "user",
                "content": (
                    "Existing conversation summary:\n\n"
                    + old_summary
                ),
            }
        )

    # Add the current conversation
    for message in messages:

        if isinstance(
            message,
            HumanMessage
        ):

            summary_messages.append(
                {
                    "role": "user",
                    "content": message.content,
                }
            )

        elif isinstance(
            message,
            AIMessage
        ):

            # Include normal AI responses
            if message.content:

                summary_messages.append(
                    {
                        "role": "assistant",
                        "content": message.content,
                    }
                )

            # Include tool calls as context
            if message.tool_calls:

                for tool_call in (
                    message.tool_calls
                ):

                    summary_messages.append(
                        {
                            "role": "assistant",
                            "content": (
                                "Called tool: "
                                + tool_call["name"]
                                + " with arguments: "
                                + json.dumps(
                                    tool_call["args"]
                                )
                            ),
                        }
                    )

        elif isinstance(
            message,
            ToolMessage
        ):

            summary_messages.append(
                {
                    "role": "user",
                    "content": (
                        "Tool result:\n"
                        + message.content
                    ),
                }
            )


    response = (
        _client()
        .chat
        .completions
        .create(
            model=config.AZURE_CHAT_DEPLOYMENT,
            temperature=0,
            messages=summary_messages,
        )
    )

    new_summary = (
        response
        .choices[0]
        .message
        .content
        or ""
    )



    messages_to_keep = messages[-6:]

    messages_to_remove = messages[:-6]


    remove_messages = [
        RemoveMessage(
            id=message.id
        )
        for message in messages_to_remove
    ]


    

    return {
        "conversation_summary": new_summary,
        "messages": remove_messages,
    }


def agent_node(state: State):

    messages = state["messages"]
    employee_id = state["employee_id"]

    # Get the existing conversation summary.
    # If there is no summary yet, use an empty string.
    conversation_summary = state.get(
        "conversation_summary",
        ""
    )

    # Get authenticated employee details
    emp = _EMPLOYEES[employee_id]

    # Build employee-specific context
    who = (
        f"You are talking to {emp['full_name']} "
        f"whose id is {emp['id']}, "
        f"based in {emp['country']}."
    )

    # Build the system prompt
    system = (
    config.PTO_SYSTEM_PROMPT
    + "\n\n"
    + who
    )

    # Keep only the most recent conversation messages
    recent_messages = trim_messages(
        messages,
        max_messages=10
    )

   



    # Messages sent to Azure OpenAI
    openai_messages = []



    openai_messages.append(
        {
            "role": "system",
            "content": system,
        }
    )




    if conversation_summary:

        openai_messages.append(
            {
                "role": "system",
                "content": (
                    "Here is a summary of the earlier "
                    "conversation. Use this summary "
                    "as context when answering the user. "
                    "Do not treat the summary as a new "
                    "user message.\n\n"
                    + conversation_summary
                ),
            }
        )




    for message in recent_messages:

        # Human message
        if isinstance(
            message,
            HumanMessage
        ):

            openai_messages.append(
                {
                    "role": "user",
                    "content": message.content,
                }
            )

        # AI message
        elif isinstance(
            message,
            AIMessage
        ):

            assistant_message = {
                "role": "assistant",
                "content": (
                    message.content
                    or ""
                ),
            }

            # Check if the AI requested tools
            if message.tool_calls:

                tool_calls = []

                for tool_call in (
                    message.tool_calls
                ):

                    tool_call_data = {
                        "id": tool_call["id"],
                        "type": "function",
                        "function": {
                            "name": (
                                tool_call["name"]
                            ),
                            "arguments": json.dumps(
                                tool_call["args"]
                            ),
                        },
                    }

                    # Add this tool call
                    tool_calls.append(
                        tool_call_data
                    )

                # Attach tool calls
                # to the assistant message
                assistant_message[
                    "tool_calls"
                ] = tool_calls

            # Add AI message
            openai_messages.append(
                assistant_message
            )

        # Tool result
        elif isinstance(
            message,
            ToolMessage
        ):

            openai_messages.append(
                {
                    "role": "tool",
                    "tool_call_id": (
                        message.tool_call_id
                    ),
                    "content": message.content,
                }
            )



    response = (
        _client()
        .chat
        .completions
        .create(
            model=config.AZURE_CHAT_DEPLOYMENT,
            temperature=0.5,
            messages=openai_messages,
            tools=TOOLS,
        )
    )

    # Get the model response
    message = (
        response
        .choices[0]
        .message
    )



    tool_calls = []

    if message.tool_calls:

        for tool_call in (
            message.tool_calls
        ):

            tool_calls.append(
                {
                    "name": (
                        tool_call
                        .function
                        .name
                    ),
                    "args": json.loads(
                        tool_call
                        .function
                        .arguments
                    ),
                    "id": (
                        tool_call.id
                    ),
                }
            )


    assistant_message = AIMessage(
        content=(
            message.content
            or ""
        ),
        tool_calls=tool_calls,
    )


    return {
        "messages": [
            assistant_message
        ]
    }





def should_continue(state: State):

    last_message = state["messages"][-1]

    # Only an AIMessage can request tools.
    if isinstance(last_message, AIMessage):

        if last_message.tool_calls:

            return "tools"

    # No tool calls means the LLM has
    # produced the final answer.
    return END


def should_summarize(state: State):

    messages = state["messages"]

    if len(messages) > 10:
        return "summarize"

    return END



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



    for tool_call in last_message.tool_calls:

        function_name = tool_call["name"]

        tool = tool_map[function_name]

        arguments = tool_call["args"]



        arguments["employee_id"] = state["employee_id"]


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


builder.add_node(
    "agent",
    agent_node
)

builder.add_node(
    "tools",
    tool_node
)

builder.add_node(
    "context_check",
    lambda state: state
)

builder.add_node(
    "summarize",
    summarize_node
)


builder.add_edge(
    START,
    "agent"
)


builder.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        END: "context_check",
    }
)


builder.add_edge(
    "tools",
    "agent"
)


builder.add_conditional_edges(
    "context_check",
    should_summarize,
    {
        "summarize": "summarize",
        END: END,
    }
)


builder.add_edge(
    "summarize",
    END
)


memory = MemorySaver()

graph = builder.compile(
    checkpointer=memory
)