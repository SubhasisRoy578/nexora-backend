"""
Nexora AI — Auth Router
Handles user registration, profile management, and onboarding.
Authentication itself is handled by Clerk — this syncs Clerk users to our DB.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.database import get_postgres_db
from app.models.user import User, UserProfile
from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse,
    UserProfileUpdate, UserProfileResponse,
    OnboardingComplete,
)
from app.middleware.auth_middleware import get_current_user

router = APIRouter()


@router.post("/sync", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def sync_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_postgres_db),
):
    """
    Called by Clerk webhook on user.created / user.updated.
    Syncs Clerk user data to our PostgreSQL database.
    """
    result = await db.execute(
        select(User).where(User.clerk_user_id == payload.clerk_user_id)
    )
    user = result.scalar_one_or_none()

    if user:
        # Update existing user
        user.email = payload.email
        if payload.full_name:
            user.full_name = payload.full_name
        if payload.avatar_url:
            user.avatar_url = payload.avatar_url
        user.updated_at = datetime.utcnow()
    else:
        # Create new user
        user = User(
            clerk_user_id=payload.clerk_user_id,
            email=payload.email,
            full_name=payload.full_name,
            avatar_url=payload.avatar_url,
        )
        db.add(user)
        await db.flush()

        # Create default profile
        profile = UserProfile(user_id=user.id)
        db.add(profile)

    await db.commit()
    await db.refresh(user)
    return user


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get the authenticated user's account info."""
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_me(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_postgres_db),
):
    """Update user display info."""
    if payload.full_name is not None:
        current_user.full_name = payload.full_name
    if payload.username is not None:
        # Check uniqueness
        existing = await db.execute(
            select(User).where(User.username == payload.username)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken",
            )
        current_user.username = payload.username
    if payload.avatar_url is not None:
        current_user.avatar_url = payload.avatar_url

    current_user.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.get("/me/profile", response_model=UserProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_postgres_db),
):
    """Get AI personalization profile."""
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
    return profile


@router.patch("/me/profile", response_model=UserProfileResponse)
async def update_profile(
    payload: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_postgres_db),
):
    """Update AI personalization profile and preferences."""
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)

    update_data = payload.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(profile, key, value)

    profile.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(profile)
    return profile


@router.post("/onboarding/complete")
async def complete_onboarding(
    payload: OnboardingComplete,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_postgres_db),
):
    """Complete the new user onboarding flow."""
    # Update profile with onboarding choices
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)

    if payload.custom_instructions:
        profile.custom_instructions = payload.custom_instructions
    profile.preferred_response_style = payload.preferred_style

    current_user.onboarding_completed = True
    current_user.updated_at = datetime.utcnow()

    await db.commit()
    return {"success": True, "message": "Welcome to Nexora AI!"}


@router.delete("/me")
async def delete_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_postgres_db),
):
    """Permanently delete user account and all data (GDPR compliance)."""
    from app.services.memory.vector_store import VectorStore
    from app.database import get_messages_collection

    # Delete vector memory
    vs = VectorStore()
    await vs.delete_namespace(f"user:{current_user.id}")
    await vs.delete_namespace(f"docs:{current_user.id}")

    # Delete MongoDB messages
    messages = get_messages_collection()
    await messages.delete_many({"user_id": str(current_user.id)})

    # Delete PostgreSQL records (cascade deletes related records)
    await db.delete(current_user)
    await db.commit()

    return {"success": True, "message": "Account and all data permanently deleted."}