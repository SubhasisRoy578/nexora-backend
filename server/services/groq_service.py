from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


async def generate_groq_response(message: str):

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": """
You are Nexora AI, an advanced AI agent platform created by Subhasis.

You are intelligent, futuristic, professional, and helpful.

Never say you are ChatGPT, Gemini, Claude, or Microsoft AI.
Always identify yourself as Nexora AI.
"""
            },
            {
                "role": "user",
                "content": message
            }
        ]
    )

    return response.choices[0].message.content