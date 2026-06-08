import requests
from app.config import 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

async def generate_openrouter_response(prompt: str):

    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {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}",
            "Content-Type": "application/json",
        },
        json={
            "model": "deepseek/deepseek-chat",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
    )

    data = response.json()

    return data["choices"][0]["message"]["content"]