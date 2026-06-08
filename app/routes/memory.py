from fastapi import APIRouter
from app.schemas import MemoryRequest

from app.ai.memory_engine import (
    store_memory,
    retrieve_memory
)

router = APIRouter()

@router.post("/memory/store")

async def save_memory(request: MemoryRequest):

    store_memory(request.text)

    return {
        "status": "stored"
    }

@router.post("/memory/search")

async def search_memory(
    request: MemoryRequest
):

    results = retrieve_memory(
        request.text
    )

    return {
        "results": results
    }