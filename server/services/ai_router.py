from server.services.groq_service import generate_groq_response
from server.services.gemini_service import generate_gemini_response
from server.services.ollama_service import generate_ollama_response

from server.memory.chat_memory import (
    add_message,
    get_conversation
)


async def route_ai(message: str):

    # Store user message
    add_message("user", message)

    # Get previous conversation
    history = get_conversation()

    # Build memory context
    context = ""

    for chat in history:
        context += f"{chat['role']}: {chat['content']}\n"

    # Final prompt with memory
    final_message = f"""
Previous Conversation:

{context}

Current User Message:
{message}
"""

    lower_message = message.lower()

    # Coding keywords
    coding_keywords = [
        "python",
        "java",
        "code",
        "program",
        "bug",
        "error",
        "javascript",
        "html",
        "css",
        "fastapi"
    ]

    # Math keywords
    math_keywords = [
        "math",
        "equation",
        "solve",
        "integration",
        "derivative",
        "matrix"
    ]

    # CODING TASK → GROQ
    if any(word in lower_message for word in coding_keywords):

        try:
            response = await generate_groq_response(final_message)

            add_message("assistant", response)

            return {
                "provider": "Groq",
                "task_type": "Coding",
                "response": response
            }

        except Exception as e:
            print("Groq Error:", e)

    # MATH TASK → GEMINI
    if any(word in lower_message for word in math_keywords):

        try:
            response = await generate_gemini_response(final_message)

            add_message("assistant", response)

            return {
                "provider": "Gemini",
                "task_type": "Math",
                "response": response
            }

        except Exception as e:
            print("Gemini Error:", e)

    # GENERAL TASK → GEMINI
    try:
        response = await generate_gemini_response(final_message)

        add_message("assistant", response)

        return {
            "provider": "Gemini",
            "task_type": "General",
            "response": response
        }

    except Exception as e:
        print("Gemini Fallback Error:", e)

    # FALLBACK → GROQ
    try:
        response = await generate_groq_response(final_message)

        add_message("assistant", response)

        return {
            "provider": "Groq",
            "task_type": "Fallback",
            "response": response
        }

    except Exception as e:
        print("Groq Fallback Error:", e)

    # FINAL OFFLINE FALLBACK → OLLAMA
    try:
        response = await generate_ollama_response(final_message)

        add_message("assistant", response)

        return {
            "provider": "Ollama",
            "task_type": "Offline",
            "response": response
        }

    except Exception as e:
        print("Ollama Error:", e)

    return {
        "provider": "None",
        "task_type": "Failed",
        "response": "All AI providers failed."
    }