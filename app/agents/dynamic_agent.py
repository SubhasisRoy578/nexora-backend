from app.llm.llm_router import ask_llm


class DynamicAgent:

    def __init__(
        self,
        name: str,
        specialty: str
    ):
        self.name = name
        self.specialty = specialty

    async def run(
        self,
        task: str
    ):

        try:

            prompt = f"""
You are a specialized AI agent named {self.name}.
Your specialty is: {self.specialty}.

Task: {task}

Respond with a detailed, helpful answer
focused on your specialty domain.
"""

            result = await ask_llm(prompt)

            return {
                "agent": self.name,
                "specialty": self.specialty,
                "task": task,
                "success": True,
                "result": result
            }

        except Exception as e:

            return {
                "agent": self.name,
                "specialty": self.specialty,
                "task": task,
                "success": False,
                "result": None,
                "error": str(e)
            }