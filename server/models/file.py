"""
Nexora AI — File Upload Model (PostgreSQL)
Tracks all uploaded files with their processing status and RAG state.
"""

import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
import enum

from app.database import Base


class FileStatus(str, enum.Enum):
    UPLOADING = "uploading"
    PROCESSING = "processing"
    READY = "ready"          # Indexed in vector DB, ready for RAG
    FAILED = "failed"


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    # File info
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)

    # Storage
    storage_provider: Mapped[str] = mapped_column(String(20), default="local")
    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    public_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # RAG processing
    status: Mapped[FileStatus] = mapped_column(
        SAEnum(FileStatus), default=FileStatus.UPLOADING
    )
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    vector_namespace: Mapped[str | None] = mapped_column(String(200), nullable=True)
    processing_error: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Metadata
    extracted_text_preview: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    extra_meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<UploadedFile id={self.id} name={self.original_filename}>"