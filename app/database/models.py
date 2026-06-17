from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Boolean,
)
from sqlalchemy.orm import relationship

from datetime import datetime

from app.database.database import Base


# =========================
# USERS
# =========================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(String, unique=True)
    email = Column(String, unique=True)

    created_at = Column(DateTime, default=datetime.utcnow)


# =========================
# CONVERSATIONS
# =========================

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"))

    title = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)


# =========================
# CHAT MEMORY
# EXISTING FEATURE PRESERVED
# =========================

class ChatMemory(Base):
    __tablename__ = "chat_memory"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(String, index=True)

    role = Column(String)

    message = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)


# =========================
# LONG TERM MEMORY
# =========================

class LongTermMemory(Base):
    __tablename__ = "long_term_memory"

    id = Column(Integer, primary_key=True)

    user_id = Column(String)

    memory_type = Column(String)

    content = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)


# =========================
# FILES
# EXISTING FEATURE PRESERVED
# =========================

class UploadedDocument(Base):
    __tablename__ = "uploaded_documents"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(String)

    filename = Column(String)

    file_type = Column(String)

    extracted_text = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)


# =========================
# AGENT EXECUTIONS
# =========================

class AgentExecution(Base):
    __tablename__ = "agent_executions"

    id = Column(Integer, primary_key=True)

    user_id = Column(String)

    agent_name = Column(String)

    task = Column(Text)

    result = Column(Text)

    status = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)


# =========================
# ANALYTICS
# =========================

class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id = Column(Integer, primary_key=True)

    user_id = Column(String)

    event_type = Column(String)

    event_data = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

class AgentTask(Base):
    
    __tablename__ = "agent_tasks"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    task_id = Column(
        String,
        unique=True,
        index=True
    )

    user_id = Column(
        String,
        index=True
    )

    goal = Column(Text)

    status = Column(
        String,
        default="pending"
    )

    result = Column(
        Text,
        nullable=True
    )

    error = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    completed_at = Column(
        DateTime,
        nullable=True
    )