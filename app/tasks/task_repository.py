import json

from datetime import datetime

from sqlalchemy import select

from app.database.database import AsyncSessionLocal

from app.database.models import AgentTask

class TaskRepository:

    async def create_task(
        self,
        task_id: str,
        user_id: str,
        goal: str
    ):

        async with AsyncSessionLocal() as db:

            task = AgentTask(
                task_id=task_id,
                user_id=user_id,
                goal=goal,
                status="running"
            )

            db.add(task)

            await db.commit()

    async def complete_task(
        self,
        task_id: str,
        result: dict
    ):

        async with AsyncSessionLocal() as db:

            query = select(
                AgentTask
            ).where(
                AgentTask.task_id == task_id
            )

            task = (
                await db.execute(query)
            ).scalar_one_or_none()

            if task:

                task.status = "completed"

                task.result = json.dumps(
                    result
                )

                task.completed_at = (
                    datetime.utcnow()
                )

                await db.commit()

    async def fail_task(
        self,
        task_id: str,
        error: str
    ):

        async with AsyncSessionLocal() as db:

            query = select(
                AgentTask
            ).where(
                AgentTask.task_id == task_id
            )

            task = (
                await db.execute(query)
            ).scalar_one_or_none()

            if task:

                task.status = "failed"

                task.error = error

                await db.commit()

    async def get_task(
        self,
        task_id: str
    ):

        async with AsyncSessionLocal() as db:

            query = select(
                AgentTask
            ).where(
                AgentTask.task_id == task_id
            )

            task = (
                await db.execute(query)
            ).scalar_one_or_none()

            return task