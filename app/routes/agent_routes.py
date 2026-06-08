from fastapi import APIRouter
from pydantic import BaseModel

from app.agents.agent_metrics import (
    agent_metrics
)

from app.agents.orchestrator import (
    run_agent_async
)

router = APIRouter()


# =====================================
# REQUEST MODEL
# =====================================

class AgentRequest(BaseModel):

    user_id: str

    goal: str


# =====================================
# AGENT LEADERBOARD
# =====================================

@router.get("/agents/rankings")
async def rankings():

    return agent_metrics.get_all_scores()


# =====================================
# BEST AGENT
# =====================================

@router.get("/agents/best")
async def best_agent():

    return agent_metrics.get_best_agent()


# =====================================
# EXECUTE AGENT
# =====================================

@router.post("/agents/run")
async def run_agent_route(
    request: AgentRequest
):

    result = await run_agent_async(
        user_goal=request.goal,
        user_id=request.user_id
    )

    return result


# =====================================
# QUICK AI CHAT
# =====================================

@router.post("/agents/chat")
async def chat_agent(
    request: AgentRequest
):

    result = await run_agent_async(
        user_goal=request.goal,
        user_id=request.user_id
    )

    return {

        "success": True,

        "goal": request.goal,

        "response":
        result.get(
            "final_answer",
            "No response"
        )
    }


# =====================================
# SYSTEM STATUS
# =====================================

@router.get("/agents/status")
async def status():

    return {

        "multi_agent": True,

        "dynamic_agents": True,

        "memory": True,

        "rag": True,

        "llm": True,

        "research": True
    }

@router.get("/agents/stats")
async def stats():

    return {
        "all_agents":
        agent_metrics.get_all_scores(),

        "best_agent":
        agent_metrics.get_best_agent()
    }    