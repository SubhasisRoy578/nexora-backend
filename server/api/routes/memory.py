"""
Nexora AI — Memory Router
Manages persistent long-term memory: view, search, add, delete.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from datetime import datetime
from typing import List

from app.database import get_postgres_db
from app.models.memory import UserMemory, MemoryType
from app.models.user import User
from app.schemas.schemas import (
    MemoryCreate, MemoryResponse,
    MemorySearchRequest, MemorySearchResult,
)
from app.services.memory.memory_service import MemoryService
from app.middleware.auth_middleware import get_current_user

router = APIRouter()
memory_service = MemoryService()


@router.get("/", response_model=List[MemoryResponse])
async def list_memories(
    memory_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_postgres_db),
):
    """List all persistent memories for the current user."""
    query = select(UserMemory).where(
        UserMemory.user_id == current_user.id,
        UserMemory.is_active == True,
    )
    if memory_type:
        query = query.where(UserMemory.memory_type == memory_type)
    query = query.order_by(UserMemory.created_at.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


@router.post("/search", response_model=List[MemorySearchResult])
async def search_memories(
    payload: MemorySearchRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Semantic search through the user's memory bank.
    Uses vector similarity to find relevant past context.
    """
    results = await memory_service.recall_relevant(
        user_id=str(current_user.id),
        query=payload.query,
        top_k=payload.top_k,
    )
    return [
        MemorySearchResult(
            id=str(i),
            content=r,
            score=1.0,
        )
        for i, r in enumerate(results)
    ]


@router.post("/", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
async def create_memory(
    payload: MemoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_postgres_db),
):
    """Manually add a memory entry (e.g. user manually saves a fact)."""
    # Store in vector DB
    await memory_service.store_in_vector_db(
        user_id=str(current_user.id),
        content=payload.content,
        metadata={"type": payload.memory_type, "manual": True},
    )

    # Store in PostgreSQL
    memory = UserMemory(
        user_id=current_user.id,
        memory_type=MemoryType(payload.memory_type),
        content=payload.content,
        importance_score=payload.importance_score,
        source_session_id=payload.source_session_id,
    )
    db.add(memory)
    await db.commit()
    await db.refresh(memory)
    return memory


@router.delete("/{memory_id}")
async def delete_memory(
    memory_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_postgres_db),
):
    """Delete a specific memory entry."""
    result = await db.execute(
        select(UserMemory).where(
            UserMemory.id == memory_id,
            UserMemory.user_id == current_user.id,
        )
    )
    memory = result.scalar_one_or_none()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")

    memory.is_active = False  # Soft delete
    await db.commit()
    return {"success": True}


@router.delete("/")
async def clear_all_memories(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_postgres_db),
):
    """
    Clear all memories for the user.
    This is the 'Reset AI Memory' button — full clean slate.
    """
    from app.services.memory.vector_store import VectorStore

    # Soft-delete from PostgreSQL
    await db.execute(
        delete(UserMemory).where(UserMemory.user_id == current_user.id)
    )

    # Delete from vector DB
    vs = VectorStore()
    await vs.delete_namespace(f"user:{current_user.id}")

    await db.commit()
    return {"success": True, "message": "All memories cleared."}


@router.get("/stats")
async def memory_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_postgres_db),
):
    """Get memory usage stats for the current user."""
    from sqlalchemy import func

    result = await db.execute(
        select(
            func.count(UserMemory.id).label("total"),
            UserMemory.memory_type,
        )
        .where(UserMemory.user_id == current_user.id, UserMemory.is_active == True)
        .group_by(UserMemory.memory_type)
    )
    rows = result.all()

    by_type = {row.memory_type: row.total for row in rows}
    total = sum(by_type.values())

    return {
        "total_memories": total,
        "by_type": by_type,
        "memory_enabled": True,
    }