from fastapi import APIRouter

from pydantic import BaseModel

from app.tasks.task_queue import (
    task_queue
)

router = APIRouter()


class AgentTaskRequest(
    BaseModel
):
    goal: str
    user_id: str = "default"


@router.post("/submit")
async def submit_task(
    request: AgentTaskRequest
):

    task_id = task_queue.submit_agent_task(
        goal=request.goal,
        user_id=request.user_id
    )

    return {
        "task_id": task_id,
        "status": "queued"
    }


@router.get("/status/{task_id}")
async def get_status(
    task_id: str
):

    return task_queue.get_status(
        task_id
    )