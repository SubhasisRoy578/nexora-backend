# ==================================================
# NEXORA AI — CHAT ROUTES
# Supports user-selected LLM provider.
# Fallback handled automatically in llm_router.
# ==================================================

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.memory.memory_manager import MemoryManager
from app.agents.orchestrator import AgentOrchestrator

router = APIRouter()

memory_manager = MemoryManager()
orchestrator = AgentOrchestrator()


# ==================================================
# REQUEST MODEL
# provider: optional — "groq" | "gemini" | "openai"
# ==================================================

class ChatRequest(BaseModel):
    user_id: str
    message: str
    provider: Optional[str] = None  # user selects LLM


# ==================================================
# SAFE HELPERS
# ==================================================

def _safe_memory_to_text(memories):

    if not memories:
        return ""

    context_lines = []

    for m in memories:
        try:
            if isinstance(m, dict):
                role = m.get("role", "unknown")
                content = m.get("content", "")
            else:
                role = getattr(m, "role", "unknown")
                content = getattr(m, "content", None)
                if content is None:
                    content = str(m)

            if content:
                context_lines.append(
                    f"{role}: {content}"
                )

        except Exception:
            continue

    return "\n".join(context_lines)


# ==================================================
# CHAT ENDPOINT
# ==================================================

@router.post("/chat")
async def chat(request: ChatRequest):

    user_id = request.user_id
    message = request.message
    provider = request.provider  # may be None

    # -------------------------------------------------
    # STEP 1: Retrieve Memories
    # -------------------------------------------------
    try:
        previous_memories = await memory_manager.search_memory_async(
            user_id=user_id,
            query=message
        )
        if not previous_memories:
            previous_memories = []

    except Exception as e:
        print(f"[Memory Search Error]: {e}")
        previous_memories = []

    # -------------------------------------------------
    # STEP 2: Build Memory Context
    # -------------------------------------------------
    memory_context = _safe_memory_to_text(previous_memories)

    # -------------------------------------------------
    # STEP 3: Profile Memory
    # -------------------------------------------------
    profile_memories = []
    try:
        profile_memories = memory_manager.get_user_profile(
            user_id=user_id
        )
        if profile_memories is None:
            profile_memories = []
    except Exception as e:
        print(f"[Profile Memory Error]: {e}")

    # -------------------------------------------------
    # STEP 4: Orchestrator Execution
    # Passes provider so LLM router uses correct model
    # -------------------------------------------------
    ai_response = ""
    result = {}

    try:
        result = await orchestrator.run(
            goal=message,
            user_id=user_id,
            provider=provider
        )

        if isinstance(result, dict):
            ai_response = result.get("final_answer") or str(result)
        else:
            ai_response = str(result)
            result = {"raw_result": ai_response}

    except Exception as e:
        print(f"[Orchestrator Error]: {e}")
        ai_response = f"Something went wrong. Please try again."
        result = {"error": str(e)}

    # -------------------------------------------------
    # STEP 5: Store Memory (non-blocking)
    # -------------------------------------------------
    try:
        await memory_manager.store_memory_async(
            user_id=user_id,
            role="user",
            content=message
        )
        if ai_response:
            await memory_manager.store_memory_async(
                user_id=user_id,
                role="assistant",
                content=ai_response
            )
    except Exception as e:
        print(f"[Memory Store Error]: {e}")

    # -------------------------------------------------
    # STEP 6: Response
    # -------------------------------------------------
    return {
        "success": True,
        "response": ai_response,
        "provider_used": provider or "groq (default)",
        "retrieved_memories": previous_memories,
        "memory_context": memory_context,
        "profile_memory": profile_memories,
        "memory_count": len(previous_memories),
        "orchestrator_enabled": True,
        "research_agent": True,
        "memory_agent": True,
        "rag_agent": True,
        "dynamic_agents": True,
        "critic_agent": True,
        "task_execution": True,
        "result": result
    }