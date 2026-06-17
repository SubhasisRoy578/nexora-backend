from app.agents.planner_agent import PlannerAgent
from app.agents.research_agent import ResearchAgent
from app.agents.memory_agent import MemoryAgent
from app.agents.rag_agent import RAGAgent
from app.agents.browser_agent import BrowserAgent

from app.router.model_router import ModelRouter


class AgentWorkflow:

    def __init__(self):

        self.planner = PlannerAgent()

        self.research_agent = ResearchAgent()

        self.memory_agent = MemoryAgent()

        self.rag_agent = RAGAgent()

        self.browser_agent = BrowserAgent()

        self.router = ModelRouter()

    async def execute(
        self,
        task: str,
        user_id: str = "default"
    ):

        plan = self.planner.create_plan(task)

        memory_data = await self.memory_agent.run(
            task,
            user_id
        )

        rag_data = await self.rag_agent.run(
            task,
            user_id
        )

        research_data = await self.research_agent.run(
            task
        )

        browser_data = await self.browser_agent.run(
            task
        )

        final_prompt = f"""
TASK:
{task}

PLAN:
{plan}

MEMORY:
{memory_data}

RAG:
{rag_data}

RESEARCH:
{research_data}

BROWSER:
{browser_data}

Generate the best final answer.
"""

        response = self.router.generate(
            final_prompt
        )

        return {
            "task": task,
            "plan": plan,
            "memory": memory_data,
            "rag": rag_data,
            "research": research_data,
            "browser": browser_data,
            "response": response
        }