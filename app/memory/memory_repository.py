# ==================================================
# NEXORA AI — MEMORY REPOSITORY
# Persistent read/write for ChatMemory +
# LongTermMemory tables in PostgreSQL.
# ==================================================

from datetime import datetime
from sqlalchemy import select, desc
from app.database.database import AsyncSessionLocal
from app.database.models import ChatMemory, LongTermMemory


class MemoryRepository:

    # ==================================================
    # STORE CHAT MESSAGE
    # Called after every user/assistant turn.
    # ==================================================

    async def store_message(
        self,
        user_id: str,
        role: str,
        content: str
    ):

        async with AsyncSessionLocal() as db:

            try:

                entry = ChatMemory(
                    user_id=user_id,
                    role=role,
                    message=content,
                    created_at=datetime.utcnow()
                )

                db.add(entry)
                await db.commit()

            except Exception as e:

                print(f"[MemoryRepo] store_message error: {e}")
                await db.rollback()

    # ==================================================
    # GET RECENT CHAT HISTORY
    # Returns last N messages for a user, oldest first.
    # ==================================================

    async def get_recent_messages(
        self,
        user_id: str,
        limit: int = 20
    ) -> list:

        async with AsyncSessionLocal() as db:

            try:

                query = (
                    select(ChatMemory)
                    .where(ChatMemory.user_id == user_id)
                    .order_by(desc(ChatMemory.created_at))
                    .limit(limit)
                )

                result = await db.execute(query)
                rows = result.scalars().all()

                # Reverse so oldest message is first
                return [
                    {
                        "role": row.role,
                        "content": row.message,
                        "timestamp": str(row.created_at)
                    }
                    for row in reversed(rows)
                ]

            except Exception as e:

                print(f"[MemoryRepo] get_recent_messages error: {e}")
                return []

    # ==================================================
    # SEARCH CHAT HISTORY (keyword match)
    # Used by memory_agent and RAG context building.
    # ==================================================

    async def search_messages(
        self,
        user_id: str,
        query: str = None,
        limit: int = 10
    ) -> list:

        async with AsyncSessionLocal() as db:

            try:

                if query:

                    # PostgreSQL ILIKE for case-insensitive keyword search
                    stmt = (
                        select(ChatMemory)
                        .where(
                            ChatMemory.user_id == user_id,
                            ChatMemory.message.ilike(f"%{query}%")
                        )
                        .order_by(desc(ChatMemory.created_at))
                        .limit(limit)
                    )

                else:

                    stmt = (
                        select(ChatMemory)
                        .where(ChatMemory.user_id == user_id)
                        .order_by(desc(ChatMemory.created_at))
                        .limit(limit)
                    )

                result = await db.execute(stmt)
                rows = result.scalars().all()

                return [
                    {
                        "role": row.role,
                        "content": row.message,
                        "timestamp": str(row.created_at)
                    }
                    for row in reversed(rows)
                ]

            except Exception as e:

                print(f"[MemoryRepo] search_messages error: {e}")
                return []

    # ==================================================
    # STORE LONG TERM MEMORY
    # Stores key facts, user preferences, summaries.
    # memory_type: "fact" | "preference" | "summary"
    # ==================================================

    async def store_long_term(
        self,
        user_id: str,
        memory_type: str,
        content: str
    ):

        async with AsyncSessionLocal() as db:

            try:

                entry = LongTermMemory(
                    user_id=user_id,
                    memory_type=memory_type,
                    content=content,
                    created_at=datetime.utcnow()
                )

                db.add(entry)
                await db.commit()

            except Exception as e:

                print(f"[MemoryRepo] store_long_term error: {e}")
                await db.rollback()

    # ==================================================
    # GET LONG TERM MEMORIES
    # ==================================================

    async def get_long_term(
        self,
        user_id: str,
        memory_type: str = None,
        limit: int = 20
    ) -> list:

        async with AsyncSessionLocal() as db:

            try:

                if memory_type:

                    stmt = (
                        select(LongTermMemory)
                        .where(
                            LongTermMemory.user_id == user_id,
                            LongTermMemory.memory_type == memory_type
                        )
                        .order_by(desc(LongTermMemory.created_at))
                        .limit(limit)
                    )

                else:

                    stmt = (
                        select(LongTermMemory)
                        .where(LongTermMemory.user_id == user_id)
                        .order_by(desc(LongTermMemory.created_at))
                        .limit(limit)
                    )

                result = await db.execute(stmt)
                rows = result.scalars().all()

                return [
                    {
                        "memory_type": row.memory_type,
                        "content": row.content,
                        "timestamp": str(row.created_at)
                    }
                    for row in rows
                ]

            except Exception as e:

                print(f"[MemoryRepo] get_long_term error: {e}")
                return []

    # ==================================================
    # GET USER PROFILE
    # Returns all user-role messages as profile snapshot.
    # ==================================================

    async def get_user_profile(
        self,
        user_id: str,
        limit: int = 20
    ) -> list:

        async with AsyncSessionLocal() as db:

            try:

                stmt = (
                    select(ChatMemory)
                    .where(
                        ChatMemory.user_id == user_id,
                        ChatMemory.role == "user"
                    )
                    .order_by(desc(ChatMemory.created_at))
                    .limit(limit)
                )

                result = await db.execute(stmt)
                rows = result.scalars().all()

                return [row.message for row in rows]

            except Exception as e:

                print(f"[MemoryRepo] get_user_profile error: {e}")
                return []


# Singleton
memory_repository = MemoryRepository()