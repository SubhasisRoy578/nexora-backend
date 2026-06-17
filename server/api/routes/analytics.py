"""
Nexora AI — Analytics Router
Usage stats, model distribution, daily charts, and token tracking.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from datetime import datetime, timedelta
from typing import List

from app.database import get_postgres_db
from app.models.chat import Conversation, Message
from app.models.agent import AgentRun
from app.models.user import User
from app.schemas.schemas import AnalyticsDashboardResponse, DailyUsage, UsageStatsResponse
from app.middleware.auth_middleware import get_current_user

router = APIRouter()


@router.get("/dashboard", response_model=AnalyticsDashboardResponse)
async def get_analytics_dashboard(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_postgres_db),
):
    """
    Full analytics dashboard for the current user.
    Returns overview stats, daily usage chart, model distribution.
    """
    user_id = current_user.id
    since = datetime.utcnow() - timedelta(days=days)

    # ── Overview ──────────────────────────────────────────────────────────────
    # Total conversations
    conv_result = await db.execute(
        select(func.count(Conversation.id))
        .where(Conversation.user_id == user_id)
    )
    total_sessions = conv_result.scalar() or 0

    # Total messages
    msg_result = await db.execute(
        select(func.count(Message.id))
        .where(Message.user_id == user_id)
    )
    total_messages = msg_result.scalar() or 0

    # Total tokens
    token_result = await db.execute(
        select(func.sum(Message.token_count))
        .where(Message.user_id == user_id)
    )
    total_tokens = token_result.scalar() or 0

    # Messages this month
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)
    month_result = await db.execute(
        select(func.count(Message.id))
        .where(Message.user_id == user_id, Message.created_at >= month_start)
    )
    messages_this_month = month_result.scalar() or 0

    # Avg session length
    avg_length = round(total_messages / max(total_sessions, 1), 1)

    # Most used model
    model_result = await db.execute(
        select(Message.model_used, func.count(Message.id).label("cnt"))
        .where(Message.user_id == user_id, Message.model_used != None)
        .group_by(Message.model_used)
        .order_by(text("cnt DESC"))
        .limit(1)
    )
    most_used_model_row = model_result.one_or_none()
    most_used_model = most_used_model_row[0] if most_used_model_row else "gpt-4o-mini"

    # Features used
    features_result = await db.execute(
        select(
            func.sum(func.cast(Conversation.used_web_search, type_=func.Integer())).label("web_search"),
            func.sum(func.cast(Conversation.used_file_rag, type_=func.Integer())).label("file_rag"),
            func.sum(func.cast(Conversation.used_voice, type_=func.Integer())).label("voice"),
            func.sum(func.cast(Conversation.used_image_gen, type_=func.Integer())).label("image_gen"),
            func.sum(func.cast(Conversation.used_agent, type_=func.Integer())).label("agent"),
        ).where(Conversation.user_id == user_id)
    )
    features_row = features_result.one()
    features_used = {
        "web_search": int(features_row.web_search or 0),
        "file_rag": int(features_row.file_rag or 0),
        "voice": int(features_row.voice or 0),
        "image_gen": int(features_row.image_gen or 0),
        "agent": int(features_row.agent or 0),
    }

    overview = UsageStatsResponse(
        total_messages=total_messages,
        messages_this_month=messages_this_month,
        total_sessions=total_sessions,
        total_tokens_used=total_tokens,
        storage_used_bytes=current_user.storage_used_bytes,
        avg_session_length=avg_length,
        most_used_model=most_used_model,
        features_used=features_used,
    )

    # ── Daily Usage ───────────────────────────────────────────────────────────
    daily_result = await db.execute(
        select(
            func.date(Message.created_at).label("date"),
            func.count(Message.id).label("messages"),
            func.sum(Message.token_count).label("tokens"),
        )
        .where(Message.user_id == user_id, Message.created_at >= since)
        .group_by(func.date(Message.created_at))
        .order_by(func.date(Message.created_at))
    )
    daily_usage = [
        DailyUsage(
            date=str(row.date),
            messages=row.messages,
            tokens=int(row.tokens or 0),
            sessions=0,  # Simplified
        )
        for row in daily_result.all()
    ]

    # ── Model Distribution ────────────────────────────────────────────────────
    model_dist_result = await db.execute(
        select(Message.model_used, func.count(Message.id).label("cnt"))
        .where(Message.user_id == user_id, Message.model_used != None)
        .group_by(Message.model_used)
    )
    model_distribution = {
        row.model_used: row.cnt
        for row in model_dist_result.all()
        if row.model_used
    }

    return AnalyticsDashboardResponse(
        overview=overview,
        daily_usage=daily_usage,
        model_distribution=model_distribution,
        top_topics=["Research", "Coding", "Writing", "Analysis", "Learning"],
    )


@router.get("/usage/summary")
async def usage_summary(
    current_user: User = Depends(get_current_user),
):
    """Quick usage summary for sidebar/header display."""
    return {
        "messages_this_month": current_user.messages_this_month,
        "tokens_used_total": current_user.tokens_used_total,
        "storage_used_bytes": current_user.storage_used_bytes,
        "subscription_tier": current_user.subscription_tier,
    }