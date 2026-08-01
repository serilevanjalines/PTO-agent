import json

from agent_runner import run_agent
from evaluation.rubrics import evaluate_correctness


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

    corretness_result = evaluate_correctness(
        user_query=test_case["input"],
        expected_answer=test_case["expected_answer"],
        actual_response=final_response,
    )

    evaluation_result = {
        "id": test_case["id"],
        "input": test_case["input"],
        "actual": {
            "tools": tool_calls,
            "response": final_response,
        },
        "evaluation": {
            "correctness": corretness_result
        },
    }

    return evaluation_result


if __name__ == "__main__":

    with open("evaluation/datasets/correctness_dataset.json") as f:
        dataset = json.load(f)

    results = []

    for test_case in dataset:
        result = run_test_case(test_case)
        results.append(result)
        print(result)

    with open(
        "evaluation/results/correctness_results.json",
        "w",
    ) as f:
        json.dump(results, f, indent=4)