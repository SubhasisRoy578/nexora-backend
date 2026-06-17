# ==================================================
# NEXORA AI — GROQ PROVIDER
# Supports: standard + streaming responses
# Model: llama-3.3-70b-versatile
# ==================================================

import os
from groq import AsyncGroq


MODEL = "llama-3.3-70b-versatile"


def _client() -> AsyncGroq:
    return AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))


# ==================================================
# STANDARD RESPONSE
# ==================================================

async def generate(
    prompt: str,
    model: str = MODEL
) -> str:

    response = await _client().chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2048,
        temperature=0.7
    )

    return response.choices[0].message.content


# ==================================================
# STREAMING RESPONSE
# Yields tokens one by one.
# ==================================================

async def stream(
    prompt: str,
    model: str = MODEL
):
    """Async generator — yields string tokens."""

    response = await _client().chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2048,
        temperature=0.7,
        stream=True
    )

    async for chunk in response:
        token = chunk.choices[0].delta.content
        if token:
            yield token