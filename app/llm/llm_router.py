# ==================================================
# NEXORA AI — LLM ROUTER
# Supports: Groq, Gemini, OpenAI
# Features:
#   - ask_llm()    → standard full response
#   - stream_llm() → async generator, token by token
#   - Automatic fallback chain on failure
#   - User-selectable provider
# ==================================================

from app.llm.providers.groq import generate as groq_generate
from app.llm.providers.groq import stream as groq_stream
from app.llm.providers.gemini import generate as gemini_generate
from app.llm.providers.gemini import stream as gemini_stream
from app.llm.providers.openai import generate as openai_generate
from app.llm.providers.openai import stream as openai_stream


# ==================================================
# PROVIDER REGISTRY
# ==================================================

PROVIDER_REGISTRY = {
    "groq": {
        "generate": groq_generate,
        "stream":   groq_stream,
    },
    "gemini": {
        "generate": gemini_generate,
        "stream":   gemini_stream,
    },
    "openai": {
        "generate": openai_generate,
        "stream":   openai_stream,
    },
}

DEFAULT_FALLBACK_CHAIN = ["groq", "gemini", "openai"]


def _build_chain(provider: str = None) -> list:
    if provider and provider in PROVIDER_REGISTRY:
        return [provider] + [
            p for p in DEFAULT_FALLBACK_CHAIN
            if p != provider
        ]
    return DEFAULT_FALLBACK_CHAIN


# ==================================================
# STANDARD (NON-STREAMING) RESPONSE
# ==================================================

async def ask_llm(
    prompt: str,
    provider: str = None
) -> str:

    chain = _build_chain(provider)
    last_error = None

    for current_provider in chain:

        generate_fn = PROVIDER_REGISTRY[current_provider]["generate"]

        try:

            print(f"[LLMRouter] Trying: {current_provider}")
            result = await generate_fn(prompt)

            if result and result.strip():
                print(f"[LLMRouter] Success: {current_provider}")
                return result

        except Exception as e:
            last_error = str(e)
            print(f"[LLMRouter] '{current_provider}' failed: {e}")
            continue

    print(f"[LLMRouter] All providers failed: {last_error}")
    return (
        "I'm having trouble connecting to my AI providers. "
        "Please try again in a moment."
    )


# ==================================================
# STREAMING RESPONSE
# Yields tokens one by one as async generator.
# Tries fallback providers if primary fails.
# ==================================================

async def stream_llm(
    prompt: str,
    provider: str = None
):
    """
    Async generator — yields string tokens one by one.
    Falls back to next provider if streaming fails.

    Usage:
        async for token in stream_llm(prompt, provider="groq"):
            print(token, end="", flush=True)
    """

    chain = _build_chain(provider)
    last_error = None

    for current_provider in chain:

        stream_fn = PROVIDER_REGISTRY[current_provider]["stream"]

        try:

            print(f"[LLMRouter] Streaming via: {current_provider}")

            async for token in stream_fn(prompt):
                yield token

            # If we got here without exception, we're done
            return

        except Exception as e:
            last_error = str(e)
            print(
                f"[LLMRouter] Stream '{current_provider}' failed: {e}. "
                f"Trying next..."
            )
            continue

    # All providers failed — yield error message as stream
    yield (
        "I'm having trouble connecting to my AI providers. "
        "Please try again in a moment."
    )


# ==================================================
# CONVENIENCE HELPERS
# ==================================================

async def ask_groq(prompt: str) -> str:
    return await ask_llm(prompt, provider="groq")

async def ask_gemini(prompt: str) -> str:
    return await ask_llm(prompt, provider="gemini")

async def ask_openai(prompt: str) -> str:
    return await ask_llm(prompt, provider="openai")

def get_available_providers() -> list:
    return list(PROVIDER_REGISTRY.keys())