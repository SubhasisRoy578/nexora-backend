from fastapi import APIRouter
from pydantic import BaseModel
from openai import OpenAI
import os
from .simplified_rag import search_rag, store_memory, get_memories

router = APIRouter()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "dummy_key"))


class ChatRequest(BaseModel):
    user_id: str
    message: str


@router.post("/chat")
async def chat(request: ChatRequest):
    # Retrieve memories and RAG context
    retrieved_memories = get_memories(request.user_id)
    rag_results = search_rag(request.message, top_k=3)
    rag_context = "\n---\n".join([chunk["text"] for chunk in rag_results])

    memory_context = "\n".join(retrieved_memories)

    # Direct OpenAI completion call
    system_prompt = (
        "You are Nexora AI, a helpful agentic assistant.\n"
        "Answer the user's message using the following contexts if relevant.\n\n"
        f"Memory context (past conversation hints):\n{memory_context}\n\n"
        f"RAG document context:\n{rag_context}\n"
    )

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.message}
            ]
        )
        ai_response = completion.choices[0].message.content
    except Exception as e:
        ai_response = f"Error calling OpenAI API: {e}"

    # Store conversation turn in memory
    store_memory(request.user_id, "user", request.message)
    store_memory(request.user_id, "assistant", ai_response)

    return {
        "response": ai_response,
        "retrieved_memories": retrieved_memories,
        "rag_context": rag_context
    }