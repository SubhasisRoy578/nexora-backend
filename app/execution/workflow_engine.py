from app.execution.task_chain import (
    TaskChain
)

class WorkflowEngine:

    def __init__(self):

        self.chain = TaskChain()

    def create_workflow(
        self,
        user_goal
    ):

        self.chain.add_task(
            "analyze_goal",
            user_goal
        )

        self.chain.add_task(
            "research",
            user_goal
        )

        self.chain.add_task(
            "generate_response",
            user_goal
        )

        return self.chain.get_tasks()