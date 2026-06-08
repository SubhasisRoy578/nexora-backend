from app.agents.orchestrator import run_agent


async def execute_agent_task(
    goal: str,
    user_id: str
):

    result = run_agent(
        user_goal=goal,
        user_id=user_id
    )

    return result