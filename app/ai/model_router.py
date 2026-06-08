from app.ai.providers.gemini_provider import (
    generate_gemini_response
)

from app.ai.providers.groq_provider import (
    generate_groq_response
)

from app.ai.providers.openrouter_provider import (
    generate_openrouter_response
)

from app.browser.browser_agent import (
    run_browser_agent
)

async def generate_response(
    model: str,
    prompt: str
):

    try:

        if "search" in prompt.lower():

            browser_result = await run_browser_agent(
                prompt
            )

            return str(browser_result)

        if model == "gemini":

            return await generate_gemini_response(
                prompt
            )

        elif model == "groq":

            return await generate_groq_response(
                prompt
            )

        elif model == "openrouter":

            return await generate_openrouter_response(
                prompt
            )

        return await generate_gemini_response(
            prompt
        )

    except Exception:

        try:

            return await generate_groq_response(
                prompt
            )

        except Exception:

            return "All AI providers failed."