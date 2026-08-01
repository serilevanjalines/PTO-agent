from app.agent_graph import graph


def run_agent(test_case):
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