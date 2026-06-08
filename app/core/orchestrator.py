from app.agents.research_agent import ResearchAgent
from app.agents.memory_agent import MemoryAgent
from app.agents.rag_agent import RAGAgent
from app.agents.browser_agent import BrowserAgent

class MultiAgentOrchestrator:

    def __init__(self):

        self.research_agent = ResearchAgent()
        self.memory_agent = MemoryAgent()
        self.rag_agent = RAGAgent()
        self.browser_agent = BrowserAgent()

    async def route(self, query: str):

        query_lower = query.lower()

        # RAG
        if "document" in query_lower or "pdf" in query_lower:
            return await self.rag_agent.run(query)

        # MEMORY
        elif "remember" in query_lower:
            return await self.memory_agent.run(query)

        # BROWSER
        elif "search" in query_lower:
            return await self.browser_agent.run(query)

        # DEFAULT RESEARCH
        else:
            return await self.research_agent.run(query)