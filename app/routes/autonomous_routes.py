from fastapi import APIRouter
from pydantic import BaseModel

from app.services.autonomous_loop import (
    AutonomousLoop
)

router = APIRouter()

loop_engine = AutonomousLoop()


class AutonomousRequest(BaseModel):

    user_id: str
    goal: str


@router.post("/run")
async def run_autonomous_task(
    request: AutonomousRequest
):

    return await loop_engine.execute_goal(
        goal=request.goal,
        user_id=request.user_id
    )