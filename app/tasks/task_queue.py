from app.workers.agent_worker import (
    run_agent_task
)


class DistributedTaskQueue:

    def submit_agent_task(
        self,
        goal,
        user_id="default"
    ):

        task = run_agent_task.delay(
            goal,
            user_id
        )

        return task.id

    def get_status(
        self,
        task_id
    ):

        task = run_agent_task.AsyncResult(
            task_id
        )

        return {
            "task_id": task.id,
            "state": task.state,
            "result": task.result
            if task.ready()
            else None
        }


task_queue = DistributedTaskQueue()