from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

async def gemini_chat(message: str):

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=message
    )

    return response.text