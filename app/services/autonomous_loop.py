from app.agents.orchestrator import AgentOrchestrator


class AutonomousLoop:

    def __init__(self):

        self.orchestrator = AgentOrchestrator()

    async def execute_goal(
        self,
        goal: str,
        user_id: str = "default",
        max_iterations: int = 10
    ):

        history = []

        current_task = goal

        for step in range(max_iterations):

            result = self.orchestrator.run(
                goal=current_task,
                user_id=user_id
            )

            history.append(result)

            plan = result.get("plan", [])

            if len(plan) == 0:
                break

            if step >= len(plan) - 1:
                break

            current_task = plan[min(step + 1, len(plan)-1)]

        return {
            "goal": goal,
            "iterations": len(history),
            "history": history,
            "status": "completed"
        }