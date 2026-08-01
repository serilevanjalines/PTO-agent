import json

from app.agent_graph import graph
from evaluation.rubrics import evaluate_faithfulness


def run_test_case(test_case):

    result = graph.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": test_case["input"],
                }
            ],
            "employee_id": test_case["employee_id"],
        },
        config={
            "configurable": {
                "thread_id": f"faithfulness_eval_{test_case['id']}"
            }
        },
    )

    messages = result["messages"]

    tool_calls = []
    tool_messages = []
    final_answer = ""

    for message in messages:

        if hasattr(message, "tool_calls"):
            for tool in message.tool_calls:
                tool_calls.append(tool["name"])

        if (
            message.type == "ai"
            and message.content
            and not message.tool_calls
        ):
            final_answer = message.content

        if(message.type=="tool"):
            tool_messages.append(message.content)

    faithfulness_result = evaluate_faithfulness(
        user_query=test_case["input"],
        tool_outputs = tool_messages,
        final_response=final_answer,
    )

    evaluation_result = {
        "id": test_case["id"],
        "input": test_case["input"],
        "actual": {
            "tools": tool_calls,
            "response": final_answer,
        },
        "evaluation": {
            "faithfulness": faithfulness_result
        },
    }

    return evaluation_result


if __name__ == "__main__":

    with open("evaluation/datasets/faithfulness_dataset.json") as f:
        dataset = json.load(f)

    results = []

    for test_case in dataset:
        result = run_test_case(test_case)
        results.append(result)
        print(result)

    with open(
        "evaluation/results/faithfulness_results.json",
        "w",
    ) as f:
        json.dump(results, f, indent=4)