# ==================================================
# NEXORA AI — MEMORY MANAGER
# Full persistent memory backed by PostgreSQL.
# Replaces the old in-memory dict implementation.
# ==================================================

import asyncio
from sentence_transformers import SentenceTransformer
from app.memory.memory_repository import memory_repository


class MemoryManager:

    _model = None

    def __init__(self):
        # No more in-memory dict — everything goes to PostgreSQL
        pass

    # ==================================================
    # LAZY LOAD EMBEDDING MODEL
    # ==================================================

    def get_embedding_model(self):

        if MemoryManager._model is None:

            try:

                MemoryManager._model = SentenceTransformer(
                    "sentence-transformers/all-MiniLM-L6-v2"
                )

                print("Embedding model loaded")

            except Exception as e:

                print(f"Embedding model unavailable: {e}")
                MemoryManager._model = None

        return MemoryManager._model

    # ==================================================
    # STORE MEMORY
    # Persists a user/assistant message to PostgreSQL.
    # Supports both async and sync callers.
    # ==================================================

    def store_memory(
        self,
        user_id: str,
        role: str,
        content: str
    ):
        """
        Sync wrapper — safe to call from both sync
        and async contexts (orchestrator, chat_routes).
        """

        try:

            loop = asyncio.get_event_loop()

            if loop.is_running():

                # Called from inside async context (FastAPI)
                asyncio.ensure_future(
                    memory_repository.store_message(
                        user_id=user_id,
                        role=role,
                        content=content
                    )
                )

            else:

                loop.run_until_complete(
                    memory_repository.store_message(
                        user_id=user_id,
                        role=role,
                        content=content
                    )
                )

        except Exception as e:

            print(f"[MemoryManager] store_memory error: {e}")

    # ==================================================
    # STORE MEMORY ASYNC
    # Use this inside async functions directly.
    # ==================================================

    async def store_memory_async(
        self,
        user_id: str,
        role: str,
        content: str
    ):

        await memory_repository.store_message(
            user_id=user_id,
            role=role,
            content=content
        )

    # ==================================================
    # SEARCH MEMORY
    # Returns matching messages from PostgreSQL.
    # Falls back to recent messages if no query.
    # ==================================================

    def search_memory(
        self,
        user_id: str,
        query: str = None
    ) -> list:
        """
        Sync wrapper for async DB search.
        Returns list of {role, content, timestamp} dicts.
        """

        try:

            loop = asyncio.get_event_loop()

            if loop.is_running():

                # Inside FastAPI async context —
                # create a new event loop for sync call
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as pool:

                    future = pool.submit(
                        asyncio.run,
                        memory_repository.search_messages(
                            user_id=user_id,
                            query=query,
                            limit=20
                        )
                    )

                    return future.result()

            else:

                return loop.run_until_complete(
                    memory_repository.search_messages(
                        user_id=user_id,
                        query=query,
                        limit=20
                    )
                )

        except Exception as e:

            print(f"[MemoryManager] search_memory error: {e}")
            return []

    # ==================================================
    # SEARCH MEMORY ASYNC
    # Use directly inside async functions.
    # ==================================================

    async def search_memory_async(
        self,
        user_id: str,
        query: str = None
    ) -> list:

        return await memory_repository.search_messages(
            user_id=user_id,
            query=query,
            limit=20
        )

    # ==================================================
    # BUILD CONTEXT STRING
    # Returns last 10 turns formatted for LLM prompt.
    # ==================================================

    def build_context(
        self,
        user_id: str,
        current_query: str = None
    ) -> str:

        try:

            loop = asyncio.get_event_loop()

            if loop.is_running():

                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as pool:

                    future = pool.submit(
                        asyncio.run,
                        memory_repository.get_recent_messages(
                            user_id=user_id,
                            limit=10
                        )
                    )

                    memories = future.result()

            else:

                memories = loop.run_until_complete(
                    memory_repository.get_recent_messages(
                        user_id=user_id,
                        limit=10
                    )
                )

            if not memories:
                return ""

            lines = [
                f"{m['role']}: {m['content']}"
                for m in memories
            ]

            return "\n".join(lines)

        except Exception as e:

            print(f"[MemoryManager] build_context error: {e}")
            return ""

    # ==================================================
    # BUILD CONTEXT ASYNC
    # Use directly inside async functions.
    # ==================================================

    async def build_context_async(
        self,
        user_id: str,
        current_query: str = None
    ) -> str:

        memories = await memory_repository.get_recent_messages(
            user_id=user_id,
            limit=10
        )

        if not memories:
            return ""

        lines = [
            f"{m['role']}: {m['content']}"
            for m in memories
        ]

        return "\n".join(lines)

    # ==================================================
    # GET USER PROFILE
    # ==================================================

    def get_user_profile(
        self,
        user_id: str
    ) -> list:

        try:

            loop = asyncio.get_event_loop()

            if loop.is_running():

                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as pool:

                    future = pool.submit(
                        asyncio.run,
                        memory_repository.get_user_profile(
                            user_id=user_id,
                            limit=20
                        )
                    )

                    return future.result()

            else:

                return loop.run_until_complete(
                    memory_repository.get_user_profile(
                        user_id=user_id,
                        limit=20
                    )
                )

        except Exception as e:

            print(f"[MemoryManager] get_user_profile error: {e}")
            return []

    # ==================================================
    # STORE LONG TERM MEMORY
    # Call this to save important facts about the user.
    # ==================================================

    async def store_long_term_async(
        self,
        user_id: str,
        memory_type: str,
        content: str
    ):

        await memory_repository.store_long_term(
            user_id=user_id,
            memory_type=memory_type,
            content=content
        )

    # ==================================================
    # GET LONG TERM MEMORIES
    # ==================================================

    async def get_long_term_async(
        self,
        user_id: str,
        memory_type: str = None
    ) -> list:

        return await memory_repository.get_long_term(
            user_id=user_id,
            memory_type=memory_type
        )