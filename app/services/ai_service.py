import os

from openai import OpenAI

from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

MODEL_MAP = {
    "GPT-4o": "openai/gpt-4o",
    "Claude 3.7": "anthropic/claude-3.7-sonnet",
    "Gemini 2.5": "google/gemini-2.5-pro",
    "DeepSeek R1": "deepseek/deepseek-r1",
    "Mistral Large": "mistralai/mistral-large",
}


async def generate_ai_response(
    message: str,
    selected_model: str,
):

    try:

        model_name = MODEL_MAP.get(
            selected_model,
            "openai/gpt-4o",
        )

        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content":
                    """
                    You are Nexora AI.

                    Use memory.

                    Use uploaded documents.

                    Use tools when needed.

                    Think step by step.
                    """
                },
                {
                    "role": "user",
                    "content": message
                }
            ],
        )

        return response.choices[0].message.content

    except Exception as e:

        print("AI ERROR:", e)

        return str(e)