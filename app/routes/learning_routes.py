from fastapi import APIRouter

from app.agents.learning_engine import (
    learning_engine
)

router = APIRouter(
    tags=["Learning System"]
)


# =====================================
# AGENT STATS
# =====================================

@router.get(
    "/learning/stats"
)
def learning_stats():

    return (
        learning_engine
        .get_agent_stats()
    )


# =====================================
# BEST AGENT
# =====================================

@router.get(
    "/learning/best-agent"
)
def best_agent():

    return (
        learning_engine
        .best_agent()
    )


# =====================================
# LEADERBOARD
# =====================================

@router.get(
    "/learning/leaderboard"
)
def leaderboard():

    return (
        learning_engine
        .leaderboard()
    )


# =====================================
# SYSTEM STATS
# =====================================

@router.get(
    "/system/stats"
)
def system_stats():

    return (
        learning_engine
        .system_stats()
    )


# =====================================
# RESET LEARNING
# =====================================

@router.post(
    "/learning/reset"
)
def reset_learning():

    learning_engine.reset()

    return {
        "status": "success",
        "message": "Learning engine reset completed"
    }