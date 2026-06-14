from app.ai.model_router import generate_response

async def coder_agent(task: str):

    prompt = f"""
You are an expert software engineer.

Write professional code for:

{task}

Return clean production-ready code.
"""

    response = await generate_response(
        "groq",
        prompt
    )

    return response