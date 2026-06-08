from fastapi import APIRouter

from app.tasks.task_manager import task_manager

router = APIRouter()


@router.get("/{task_id}")
async def get_task(task_id: str):

    task = task_manager.get_task(task_id)

    if not task:

        return {
            "status": "not_found"
        }

    return task