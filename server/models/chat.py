"""
Nexora AI — Chat Models (PostgreSQL / SQLAlchemy)
Conversation metadata lives here; full message content is in MongoDB for flexibility.
"""

import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Text, Integer, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import enum

from app.database import Base


class ConversationMode(str, enum.Enum):
    PERSISTENT = "persistent"
    TEMPORARY = "temporary"


class ConversationStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class Conversation(Base):
    """
    Metadata for each chat conversation.
    Persistent conversations are stored here + MongoDB.
    Temporary conversations are Redis-only (not here).
    """
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    # Metadata
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    mode: Mapped[ConversationMode] = mapped_column(
        SAEnum(ConversationMode), default=ConversationMode.PERSISTENT
    )
    status: Mapped[ConversationStatus] = mapped_column(
        SAEnum(ConversationStatus), default=ConversationStatus.ACTIVE
    )

    # Model info
    primary_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    model_mode: Mapped[str] = mapped_column(String(20), default="auto")

    # Stats
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    token_count: Mapped[int] = mapped_column(Integer, default=0)

    # Features used
    used_web_search: Mapped[bool] = mapped_column(Boolean, default=False)
    used_file_rag: Mapped[bool] = mapped_column(Boolean, default=False)
    used_voice: Mapped[bool] = mapped_column(Boolean, default=False)
    used_image_gen: Mapped[bool] = mapped_column(Boolean, default=False)
    used_agent: Mapped[bool] = mapped_column(Boolean, default=False)

    # File attachments
    file_ids: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<Conversation id={self.id} session={self.session_id}>"


class Message(Base):
    """
    Lightweight message metadata in PostgreSQL.
    Full content is in MongoDB messages collection for scale.
    """
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )

    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user | assistant | system
    model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    token_count: Mapped[int] = mapped_column(Integer, default=0)

    # Feature flags for this message
    has_files: Mapped[bool] = mapped_column(Boolean, default=False)
    has_images: Mapped[bool] = mapped_column(Boolean, default=False)
    used_tools: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Message id={self.id} role={self.role}>"