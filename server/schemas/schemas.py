"""
Nexora AI — User Schemas (Pydantic)
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
import uuid


class UserCreate(BaseModel):
    clerk_user_id: str
    email: EmailStr
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    username: Optional[str] = Field(None, min_length=3, max_length=30)
    avatar_url: Optional[str] = None


class UserProfileUpdate(BaseModel):
    custom_instructions: Optional[str] = Field(None, max_length=2000)
    preferred_response_style: Optional[str] = Field(
        None, pattern="^(balanced|concise|detailed|creative|technical)$"
    )
    preferred_language: Optional[str] = Field(None, max_length=10)
    ai_name_preference: Optional[str] = Field(None, max_length=50)
    preferred_model_mode: Optional[str] = Field(
        None, pattern="^(auto|swift_mind|aether_core)$"
    )
    default_provider: Optional[str] = Field(
        None, pattern="^(openai|anthropic|google)$"
    )
    enable_memory: Optional[bool] = None
    enable_web_search: Optional[bool] = None
    enable_voice: Optional[bool] = None
    show_thinking_process: Optional[bool] = None
    theme: Optional[str] = Field(None, pattern="^(dark|light|system)$")
    sidebar_collapsed: Optional[bool] = None


class UserResponse(BaseModel):
    id: uuid.UUID
    clerk_user_id: str
    email: str
    username: Optional[str]
    full_name: Optional[str]
    avatar_url: Optional[str]
    subscription_tier: str
    is_active: bool
    onboarding_completed: bool
    messages_this_month: int
    created_at: datetime

    class Config:
        from_attributes = True


class UserProfileResponse(BaseModel):
    custom_instructions: Optional[str]
    preferred_response_style: str
    preferred_language: str
    ai_name_preference: Optional[str]
    preferred_model_mode: str
    enable_memory: bool
    enable_web_search: bool
    enable_voice: bool
    show_thinking_process: bool
    theme: str
    sidebar_collapsed: bool

    class Config:
        from_attributes = True


class OnboardingComplete(BaseModel):
    use_case: str  # "study" | "work" | "creative" | "coding" | "research"
    custom_instructions: Optional[str] = None
    preferred_style: str = "balanced"