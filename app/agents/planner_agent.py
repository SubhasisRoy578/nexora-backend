from app.llm.llm_router import ask_llm


class PlannerAgent:

    async def create_plan_async(
        self,
        task: str
    ) -> list:

        try:

            prompt = f"""
You are a planning agent for Nexora AI.

Break down this task into clear execution steps:
Task: {task}

Rules:
- Return ONLY a numbered list of steps
- Each step must be actionable
- Maximum 6 steps
- No explanations, just steps

Example format:
1. Search for relevant information
2. Analyze the findings
3. Generate a response
"""

            raw = await ask_llm(prompt)

            steps = []
            for line in raw.splitlines():
                line = line.strip()
                if line and line[0].isdigit():
                    # Strip leading "1. " or "1) "
                    step = line.lstrip("0123456789").lstrip(". )").strip()
                    if step:
                        steps.append(step)

            if not steps:
                steps = self._keyword_plan(task)

            return steps

        except Exception:
            return self._keyword_plan(task)

    def _keyword_plan(
        self,
        task: str
    ) -> list:
        """Fallback keyword-based planner."""

        task_lower = task.lower()
        steps = []

        if any(w in task_lower for w in ["research", "find", "search", "latest", "news"]):
            steps += [
                "Search the web for relevant information",
                "Collect and filter results",
                "Summarize key findings"
            ]

        if any(w in task_lower for w in ["build", "create", "develop", "make"]):
            steps += [
                "Analyze requirements",
                "Design the architecture",
                "Generate implementation"
            ]

        if any(w in task_lower for w in ["analyze", "compare", "evaluate"]):
            steps += [
                "Gather data on the subject",
                "Compare key aspects",
                "Provide analysis and recommendation"
            ]

        if any(w in task_lower for w in ["automate", "browser", "navigate", "open"]):
            steps += [
                "Open browser agent",
                "Navigate to target",
                "Execute automation task"
            ]

        if any(w in task_lower for w in ["remember", "memory", "history"]):
            steps += [
                "Retrieve conversation memory",
                "Contextualize with history",
                "Respond with context"
            ]

        if not steps:
            steps = [
                "Understand the user's intent",
                "Retrieve relevant context",
                "Generate a helpful response"
            ]

        return steps


    def create_plan(self, task: str) -> list:
        """Sync fallback used by orchestrator's non-async plan call."""
        return self._keyword_plan(task)


planner_agent = PlannerAgent()


def create_plan(task: str) -> list:
    return planner_agent.create_plan(task)