import json

from app.agent_graph import graph
from evaluation.rubrics import safety_evaluator


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
                "thread_id": f"intent_eval_{test_case['id']}"
            }
        },
    )

    messages = result["messages"]

    tool_calls = []
    final_response = ""

    for message in messages:

        if hasattr(message, "tool_calls"):
            for tool in message.tool_calls:
                tool_calls.append(tool["name"])

        if (
            message.type == "ai"
            and message.content
            and not message.tool_calls
        ):
            final_response = message.content

    response_result = safety_evaluator(
        user_query=test_case["input"],
        final_response=final_response,
    )

    evaluation_result = {
        "id": test_case["id"],
        "input": test_case["input"],
        "AI response": {
            "AI_replied": final_response,
        },
        "evaluation": {
            "safety_evaluation": response_result
        },
    }

    return evaluation_result


if __name__ == "__main__":

    with open("evaluation/datasets/safety_dataset.json") as f:
        dataset = json.load(f)

    results = []

    for test_case in dataset:
        result = run_test_case(test_case)
        results.append(result)
        print(result)

    with open(
        "evaluation/results/safety_results.json",
        "w",
    ) as f:
        json.dump(results, f, indent=4)