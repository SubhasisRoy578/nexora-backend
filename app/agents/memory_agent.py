from app.memory.memory_manager import MemoryManager


class MemoryAgent:

    def __init__(self):

        self.memory = MemoryManager()

    async def run(
        self,
        query: str,
        user_id: str = "default"
    ):

        try:

            memories = self.memory.search_memory(
                user_id=user_id,
                query=query
            )

            return {
                "agent": "memory_agent",
                "success": True,
                "memories": memories
            }

        except Exception as e:

            return {
                "agent": "memory_agent",
                "success": False,
                "error": str(e)
            }