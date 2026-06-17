# ==================================================
# NEXORA AI — OPENAI PROVIDER
# Supports: standard + streaming responses
# Model: gpt-4o-mini
# ==================================================

import os
from openai import AsyncOpenAI


MODEL = "gpt-4o-mini"


def _client() -> AsyncOpenAI:
    return AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


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