# app/models/document.py
import json
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from sqlalchemy.types import TypeDecorator
from app.database import Base, HAS_PGVECTOR


class SafeVector(TypeDecorator):
    """
    A custom SQLAlchemy type that maps to:
      - pgvector's Vector type (dimension 1536) on PostgreSQL if pgvector is available.
      - TEXT type (JSON serialized array) on SQLite or if pgvector is missing.
    """
    impl = Text
    cache_ok = True

    def __init__(self, dim=1536, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dim = dim

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql' and HAS_PGVECTOR:
            try:
                from pgvector.sqlalchemy import Vector
                return dialect.type_descriptor(Vector(self.dim))
            except ImportError:
                pass
        return dialect.type_descriptor(Text)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == 'postgresql' and HAS_PGVECTOR:
            return value
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == 'postgresql' and HAS_PGVECTOR:
            return list(value)
        try:
            return json.loads(value)
        except Exception:
            return value


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(512), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    embedding = Column(SafeVector(1536), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<DocumentChunk id={self.id} file={self.filename} chunk={self.chunk_index}>"

    def to_dict(self):
        """Convert chunk to dictionary for API responses."""
        return {
            "id": self.id,
            "filename": self.filename,
            "chunk_index": self.chunk_index,
            "text": self.text[:500] + "..." if len(self.text) > 500 else self.text,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
