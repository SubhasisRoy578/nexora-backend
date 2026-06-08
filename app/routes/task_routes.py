from fastapi import APIRouter
from pydantic import BaseModel

from app.tasks.task_manager import (
    task_manager
)

from app.tasks.agent_tasks import (
    execute_agent_task
)

router = APIRouter()


class AgentTaskRequest(BaseModel):

    user_id: str

    goal: str


@router.post("/agent")
async def create_agent_task(
    request: AgentTaskRequest
):

    task_id = await task_manager.create_task(
        "agent_execution",
        execute_agent_task(
            request.goal,
            request.user_id
        )
    )

    return {
        "task_id": task_id,
        "status": "queued"
    }


@router.get("/{task_id}")
async def get_task_status(
    task_id: str
):

    return task_manager.get_task(
        task_id
    )


@router.get("/")
async def list_tasks():

    return task_manager.get_all_tasks()