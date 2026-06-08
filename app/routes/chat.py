from fastapi import APIRouter
from app.schemas import ChatRequest

from app.ai.model_router import generate_response
from app.ai.memory_engine import store_memory
from app.ai.rag_pipeline import build_context

router = APIRouter()

@router.post("/chat")
async def chat(request: ChatRequest):

    enhanced_prompt = build_context(
        request.message
    )

    response = await generate_response(
        request.model,
        enhanced_prompt
    )

    store_memory(request.message)
    store_memory(response)

    return {
        "response": response
    }