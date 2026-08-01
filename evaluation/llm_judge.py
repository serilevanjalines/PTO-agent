import json

from app.llm_client import _client
from app import config


def run_llm_judge(prompt):

    client = _client()

    response = client.chat.completions.create(
        model=config.AZURE_CHAT_DEPLOYMENT,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=0,
    )

    content = response.choices[0].message.content

    try:
        return json.loads(content)

    except Exception:
        return {
            "score": 0,
            "reason": "Judge returned invalid JSON"
        }