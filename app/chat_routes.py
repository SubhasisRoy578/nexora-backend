from fastapi import APIRouter
from pydantic import BaseModel

from .memory.memory_manager import MemoryManager
from .rag.rag_engine import RAGEngine

router = APIRouter()

memory_manager = MemoryManager()
rag_engine = RAGEngine()


class ChatRequest(BaseModel):
    user_id: str
    message: str


@router.post("/chat")
async def chat(request: ChatRequest):
    retrieved_memories = memory_manager.search_memory(
        user_id=request.user_id,
        query=request.message
    )

    rag_context = rag_engine.generate_context(
        user_id=request.user_id,
        query=request.message
    )

    memory_context = "\n".join(retrieved_memories)

    ai_response = f"""
MEMORY CONTEXT:
{memory_context}

RAG CONTEXT:
{rag_context}

NEXORA RESPONSE:
I found relevant memories and knowledge.
You asked: {request.message}
"""

    memory_manager.store_memory(
        user_id=request.user_id,
        role="user",
        content=request.message
    )

    memory_manager.store_memory(
        user_id=request.user_id,
        role="assistant",
        content=ai_response
    )

    return {
        "response": ai_response,
        "retrieved_memories": retrieved_memories,
        "rag_context": rag_context
    }
