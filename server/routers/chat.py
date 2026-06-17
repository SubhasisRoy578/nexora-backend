from server.services.memory_service import (
    add_message,
    get_memory
)
from fastapi import APIRouter
from server.models.chat_model import ChatRequest

from server.services.gemini_service import generate_gemini_response
from server.services.groq_service import generate_groq_response
from server.services.ollama_service import generate_ollama_response

from server.services.memory_service import (
    add_message,
    get_memory
)

router = APIRouter()


@router.post("/chat/")
async def chat(request: ChatRequest):

    # Store User Message
    add_message("user", request.message)

    # Get Full Conversation
    memory = get_memory()

    # Convert memory to text
    conversation_text = ""

    for msg in memory:
        conversation_text += f"{msg['role']}: {msg['content']}\n"

    try:

        ai_response = await generate_gemini_response(conversation_text)

        provider = "Gemini"

    except Exception as gemini_error:

        print("Gemini Failed:", gemini_error)

        try:

            ai_response = await generate_groq_response(conversation_text)

            provider = "Groq"

        except Exception as groq_error:

            print("Groq Failed:", groq_error)

            try:

                ai_response = await generate_ollama_response(conversation_text)

                provider = "Ollama"

            except Exception as ollama_error:

                print("Ollama Failed:", ollama_error)

                return {
                    "success": False,
                    "message": "All AI providers failed."
                }

    # Store AI Response
    add_message("assistant", ai_response)

    return {
        "success": True,
        "provider": provider,
        "memory_size": len(memory),
        "user_message": request.message,
        "ai_response": ai_response
    }