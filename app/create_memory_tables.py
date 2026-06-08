# ==================================================
# NEXORA AI — DATABASE MIGRATION
# Run this ONCE to create all tables in PostgreSQL.
# Usage: python create_memory_tables.py
# ==================================================

import asyncio
from app.database.database import engine, Base

# Import all models so Base knows about them
from app.database.models import (
    User,
    Conversation,
    ChatMemory,
    LongTermMemory,
    UploadedDocument,
    AgentExecution,
    AnalyticsEvent,
    AgentTask
)


async def create_tables():

    async with engine.begin() as conn:

        await conn.run_sync(Base.metadata.create_all)

        print("All tables created successfully:")
        print("  - users")
        print("  - conversations")
        print("  - chat_memory        ← persistent chat history")
        print("  - long_term_memory   ← long-term user facts")
        print("  - uploaded_documents")
        print("  - agent_executions")
        print("  - analytics_events")
        print("  - agent_tasks")


if __name__ == "__main__":
    asyncio.run(create_tables())