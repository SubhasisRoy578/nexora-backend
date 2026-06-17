from fastapi import APIRouter
from pydantic import BaseModel

from app.agents.orchestrator import run_agent

router = APIRouter()

class AgentRequest(BaseModel):
    goal: str

@router.post("/agent")

async def agent_route(request: AgentRequest):

    result = run_agent(request.goal)

    return result