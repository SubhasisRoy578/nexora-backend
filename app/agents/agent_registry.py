# ==================================================
# NEXORA AI — AGENT REGISTRY
# Central registry for all agents.
# Fallback chains defined per agent type.
# ==================================================

from app.agents.research_agent import ResearchAgent
from app.agents.rag_agent import RAGAgent
from app.agents.memory_agent import MemoryAgent
from app.agents.browser_agent import BrowserAgent
from app.agents.critic_agent import CriticAgent
from app.agents.coding_agent import CodingAgent


def build_registry() -> dict:

    return {

        "research": {
            "agent": ResearchAgent(),
            "description": "Searches the web for real-time information",
            "fallbacks": ["rag", "memory"]
        },

        "rag": {
            "agent": RAGAgent(),
            "description": "Retrieves context from uploaded documents",
            "fallbacks": ["memory", "research"]
        },

        "memory": {
            "agent": MemoryAgent(),
            "description": "Retrieves past conversation history",
            "fallbacks": ["rag"]
        },

        "browser": {
            "agent": BrowserAgent(),
            "description": "Browses websites and extracts content",
            "fallbacks": ["research"]
        },

        "critic": {
            "agent": CriticAgent(),
            "description": "Evaluates and scores agent responses",
            "fallbacks": []
        },

        "coding": {
            "agent": CodingAgent(),
            "description": "Generates, executes, debugs, and explains Python code",
            "fallbacks": ["research"]
        },
    }


_registry = None


def get_registry() -> dict:
    global _registry
    if _registry is None:
        _registry = build_registry()
    return _registry