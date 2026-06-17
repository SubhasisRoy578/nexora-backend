import os

from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GOOGLE_API_KEY")
)


async def generate_gemini_response(message: str):

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=message
    )

    return response.text