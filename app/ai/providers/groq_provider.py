from groq import Groq

from app.config import settings


client = Groq(
    api_key=settings.GROQ_API_KEY
)


async def generate_groq_response(
    prompt: str
):

    completion = client.chat.completions.create(

        model="llama-3.3-70b-versatile",

        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]

    )

    return completion.choices[0].message.content