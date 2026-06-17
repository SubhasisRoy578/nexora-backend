import os
import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

URL = "https://openrouter.ai/api/v1/chat/completions"


async def generate_openrouter_response(message: str):

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "deepseek/deepseek-r1-0528:free",

        "messages": [
            {
                "role": "user",
                "content": message
            }
        ]
    }

    response = requests.post(
        URL,
        headers=headers,
        json=payload
    )

    data = response.json()

    print(data)

    if "choices" in data:
        return data["choices"][0]["message"]["content"]

    elif "error" in data:
        return f"OpenRouter Error: {data['error']['message']}"

    else:
        return "Unknown OpenRouter response error."