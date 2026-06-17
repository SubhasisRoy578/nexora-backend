"""
Nexora AI — User Model (PostgreSQL / SQLAlchemy)
Stores core user account data and subscription info.
Personalization, preferences, and AI profile live in UserProfile.
"""

import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Text, Integer, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import enum

from app.database import Base


class SubscriptionTier(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    TEAM = "team"
    ENTERPRISE = "enterprise"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    clerk_user_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Subscription
    subscription_tier: Mapped[SubscriptionTier] = mapped_column(
        SAEnum(SubscriptionTier), default=SubscriptionTier.FREE, nullable=False
    )
    subscription_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Usage tracking
    messages_this_month: Mapped[int] = mapped_column(Integer, default=0)
    tokens_used_total: Mapped[int] = mapped_column(Integer, default=0)
    storage_used_bytes: Mapped[int] = mapped_column(Integer, default=0)

    # Flags
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    profile: Mapped["UserProfile"] = relationship(
        "UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"

    @property
    def is_pro(self) -> bool:
        return self.subscription_tier in (
            SubscriptionTier.PRO,
            SubscriptionTier.TEAM,
            SubscriptionTier.ENTERPRISE,
        )


class UserProfile(Base):
    """
    Extended AI personalization profile.
    Stores user preferences, custom instructions, and AI-learned attributes.
    """
    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        unique=True,
        index=True,
    )

    # AI Personalization
    custom_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    preferred_response_style: Mapped[str] = mapped_column(String(50), default="balanced")
    preferred_language: Mapped[str] = mapped_column(String(10), default="en")
    ai_name_preference: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Model preferences
    preferred_model_mode: Mapped[str] = mapped_column(String(20), default="auto")
    default_provider: Mapped[str] = mapped_column(String(20), default="openai")

    # Feature flags
    enable_memory: Mapped[bool] = mapped_column(Boolean, default=True)
    enable_web_search: Mapped[bool] = mapped_column(Boolean, default=True)
    enable_voice: Mapped[bool] = mapped_column(Boolean, default=False)
    show_thinking_process: Mapped[bool] = mapped_column(Boolean, default=False)

    # UI preferences
    theme: Mapped[str] = mapped_column(String(20), default="dark")
    sidebar_collapsed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="profile")