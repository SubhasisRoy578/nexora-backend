import google.generativeai as genai
from app.config import AIzaSyCieUfu0s7Teh_PoUWYPu_nIzLXfqhcpto

genai.configure(api_key=AIzaSyCieUfu0s7Teh_PoUWYPu_nIzLXfqhcpto)

model = genai.GenerativeModel("gemini-2.0-flash")

async def generate_gemini_response(prompt: str):
    response = model.generate_content(prompt)
    return response.text