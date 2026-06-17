"""
Nexora AI — Memory & Agent Models (PostgreSQL / SQLAlchemy)
"""

import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Text, Integer, Float, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
import enum

from app.database import Base


# ── Memory ────────────────────────────────────────────────────────────────────

class MemoryType(str, enum.Enum):
    EPISODIC = "episodic"       # Conversation events
    SEMANTIC = "semantic"       # Facts and knowledge
    PREFERENCE = "preference"   # User preferences
    SKILL = "skill"             # Learned capabilities


class UserMemory(Base):
    """
    Structured memory entries for long-term AI personalization.
    Complements the vector DB semantic search with queryable records.
    """
    __tablename__ = "user_memories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    memory_type: Mapped[MemoryType] = mapped_column(
        SAEnum(MemoryType), default=MemoryType.EPISODIC
    )

    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Vector DB reference
    vector_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    embedding_model: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Metadata
    importance_score: Mapped[float] = mapped_column(Float, default=0.5)
    access_count: Mapped[int] = mapped_column(Integer, default=0)
    source_session_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    extra: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_accessed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<UserMemory id={self.id} type={self.memory_type}>"


# ── Agents ────────────────────────────────────────────────────────────────────

class AgentRunStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentRun(Base):
    """
    Tracks each agent execution — steps, tools used, output.
    """
    __tablename__ = "agent_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    session_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    # Task
    task_description: Mapped[str] = mapped_column(Text, nullable=False)
    agent_type: Mapped[str] = mapped_column(String(50), default="single")  # single | crew | graph

    # Execution
    status: Mapped[AgentRunStatus] = mapped_column(
        SAEnum(AgentRunStatus), default=AgentRunStatus.PENDING
    )
    tools_used: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    steps: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    result: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Performance
    iterations: Mapped[int] = mapped_column(Integer, default=0)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<AgentRun id={self.id} status={self.status}>"


class AgentTool(Base):
    """Registry of available tools/functions for agent use."""
    __tablename__ = "agent_tools"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    requires_auth: Mapped[bool] = mapped_column(Boolean, default=False)
    schema: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<AgentTool name={self.name}>"