# ==================================================
# NEXORA AI — GEMINI PROVIDER
# Supports: standard + streaming responses
# Model: gemini-1.5-flash
# ==================================================

import os
import asyncio
import google.generativeai as genai


MODEL = "gemini-1.5-flash"


def _model():
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    return genai.GenerativeModel(MODEL)


# ==================================================
# STANDARD RESPONSE
# ==================================================

async def generate(
    prompt: str,
    model: str = MODEL
) -> str:

    loop = asyncio.get_event_loop()

    response = await loop.run_in_executor(
        None,
        lambda: _model().generate_content(prompt)
    )

    return response.text


# ==================================================
# STREAMING RESPONSE
# Yields tokens one by one.
# ==================================================

async def stream(
    prompt: str,
    model: str = MODEL
):
    """Async generator — yields string tokens."""

    loop = asyncio.get_event_loop()

    # Gemini streaming is sync — run in executor
    def _stream_sync():
        return _model().generate_content(
            prompt,
            stream=True
        )

    response = await loop.run_in_executor(None, _stream_sync)

    for chunk in response:
        if chunk.text:
            yield chunk.text
            await asyncio.sleep(0)