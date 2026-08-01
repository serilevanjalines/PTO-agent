import json

from agent_runner import run_agent
from evaluation.rubrics import evaluate_intent


def run_test_case(test_case):

    result = run_agent(test_case)

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

    intent_result = evaluate_intent(
        user_query=test_case["input"],
        expected_intent=test_case["expected_intent"],
        actual_tools=tool_calls,
        final_response=final_response,
    )

    evaluation_result = {
        "id": test_case["id"],
        "input": test_case["input"],
        "actual": {
            "tools": tool_calls,
            "response": final_response,
        },
        "evaluation": {
            "intent": intent_result
        },
    }

    return evaluation_result


if __name__ == "__main__":

    with open("evaluation/datasets/intent_dataset.json") as f:
        dataset = json.load(f)

    results = []

    for test_case in dataset:
        result = run_test_case(test_case)
        results.append(result)
        print(result)

    with open(
        "evaluation/results/intent_results.json",
        "w",
    ) as f:
        json.dump(results, f, indent=4)