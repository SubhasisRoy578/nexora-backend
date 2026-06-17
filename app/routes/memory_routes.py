from fastapi import APIRouter
from pydantic import BaseModel

from app.memory.memory_manager import MemoryManager

router = APIRouter()

memory_manager = MemoryManager()


# ==========================
# REQUEST MODELS
# ==========================

class MemoryRequest(BaseModel):
    user_id: str
    content: str


class SearchRequest(BaseModel):
    user_id: str
    query: str


class FactRequest(BaseModel):
    user_id: str
    fact: str


# ==========================
# STORE MEMORY
# ==========================

@router.post("/memory/store")
async def store_memory(request: MemoryRequest):

    memory_manager.store_memory(
        user_id=request.user_id,
        role="user",
        content=request.content
    )

    return {
        "message": "Memory stored successfully"
    }


# ==========================
# SEARCH MEMORY
# ==========================

@router.post("/memory/search")
async def search_memory(request: SearchRequest):

    memories = memory_manager.search_memory(
        user_id=request.user_id,
        query=request.query
    )

    return {
        "memories": memories
    }


# ==========================
# STORE USER FACT
# ==========================

@router.post("/memory/fact")
async def store_fact(request: FactRequest):

    memory_manager.save_user_fact(
        user_id=request.user_id,
        fact=request.fact
    )

    return {
        "message": "Fact stored successfully"
    }


# ==========================
# GET USER PROFILE
# ==========================

@router.get("/memory/profile/{user_id}")
async def get_profile(user_id: str):

    profile = memory_manager.get_user_profile(
        user_id=user_id
    )

    return {
        "user_id": user_id,
        "profile": profile
    }


# ==========================
# BUILD MEMORY CONTEXT
# ==========================

@router.post("/memory/context")
async def build_context(request: SearchRequest):

    context = memory_manager.build_context(
        user_id=request.user_id,
        current_query=request.query
    )

    return {
        "context": context
    }