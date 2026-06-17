import requests

OLLAMA_URL = "http://localhost:11434/api/generate"


async def generate_ollama_response(message: str):

    system_prompt = """
You are Nexora AI, an advanced AI agent platform created by Subhasis.

Your personality:
- intelligent
- professional
- futuristic
- concise
- helpful

Rules:
- Never say you are ChatGPT
- Never say you are Gemini
- Never say you are Claude
- Never say you are Microsoft AI
- Always identify yourself as Nexora AI
"""

    full_prompt = f"""
{system_prompt}

User: {message}

Nexora AI:
"""

    payload = {
        "model": "phi3",
        "prompt": full_prompt,
        "stream": False
    }

    response = requests.post(OLLAMA_URL, json=payload)

    data = response.json()

    return data["response"]