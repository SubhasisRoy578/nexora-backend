from app.workers.celery_app import celery_app

from app.agents.orchestrator import AgentOrchestrator


@celery_app.task(
    bind=True,
    name="run_agent_task"
)
def run_agent_task(
    self,
    goal,
    user_id="default"
):

    orchestrator = AgentOrchestrator()

    result = orchestrator.run_sync(
        goal=goal,
        user_id=user_id
    )

    return result