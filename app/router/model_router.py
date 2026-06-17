from google import genai
from app.core.config import settings


class ModelRouter:
    def __init__(self):
        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY
        )

    def generate(
        self,
        prompt: str,
        model_name: str = "gemini-2.5-flash",
    ):
        response = self.client.models.generate_content(
            model=model_name,
            contents=prompt,
        )

        return response.text