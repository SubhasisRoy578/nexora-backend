import uuid

from datetime import datetime


class TaskManager:

    def __init__(self):

        self.tasks = {}

    async def create_task(
        self,
        task_name,
        coroutine
    ):

        task_id = str(
            uuid.uuid4()
        )

        self.tasks[task_id] = {

            "task_name":
            task_name,

            "status":
            "running",

            "created_at":
            str(datetime.utcnow())
        }

        return task_id

    def complete_task(
        self,
        task_id,
        result
    ):

        self.tasks[task_id] = {

            "status":
            "completed",

            "result":
            result,

            "completed_at":
            str(datetime.utcnow())
        }

    def get_task(
        self,
        task_id
    ):

        return self.tasks.get(
            task_id
        )


task_manager = TaskManager()