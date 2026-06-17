import google.generativeai as genai
import openai
import os

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)

openai.api_key = os.getenv("OPENAI_API_KEY")

def ask_llm(prompt: str, model: str):

    try:

        if model == "gemini":

            gemini_model = genai.GenerativeModel(
                "gemini-1.5-flash"
            )

            response = gemini_model.generate_content(prompt)

            return response.text

        elif model == "openai":

            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            return response.choices[0].message.content

    except Exception:

        if model == "gemini":
            return ask_llm(prompt, "openai")

        return "All models failed."