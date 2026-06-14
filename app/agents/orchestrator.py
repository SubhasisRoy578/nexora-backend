# ==================================================
# NEXORA AI — ORCHESTRATOR
# Full agent pipeline with:
# - Persistent memory (PostgreSQL)
# - Web search (DuckDuckGo, 2026 fresh)
# - Multi-LLM with fallback (Groq → Gemini → OpenAI)
# - Agent fallback chain
# - Concurrent agent execution
# ==================================================

from datetime import datetime
import asyncio
import uuid

from app.agents.learning_engine import learning_engine
from app.tasks.task_service import task_repository
from app.llm.llm_router import ask_llm
from app.agents.planner_agent import create_plan
from app.agents.critic_agent import CriticAgent
from app.agents.agent_factory import agent_factory
from app.agents.specialization_detector import detect_specialized_agent
from app.agents.agent_registry import get_registry
from app.tools.tool_registry import ToolRegistry
from app.memory.memory_manager import MemoryManager
from app.rag.rag_engine import RAGEngine
from app.messaging.agent_bus import agent_bus


class AgentOrchestrator:

    def __init__(self):

        self.registry = ToolRegistry()
        self.memory = MemoryManager()
        self.rag = RAGEngine()
        self.critic_agent = CriticAgent()
        self.agent_factory = agent_factory

    # ==================================================
    # TOOL DETECTION
    # ==================================================

    def detect_tool(self, goal: str):

        goal_lower = goal.lower()

        if any(w in goal_lower for w in [
            "calculate", "math", "equation", "+"
        ]):
            return "calculator"

        if any(w in goal_lower for w in [
            "python", "code", "program"
        ]):
            return "python_executor"

        if any(w in goal_lower for w in [
            "pdf", "document", "file"
        ]):
            return "file_reader"

        if any(w in goal_lower for w in [
            "search", "research", "internet",
            "web", "latest", "news", "current",
            "today", "2026", "update"
        ]):
            return "web_search"

        return None

    # ==================================================
    # AGENT DETECTION
    # ==================================================

    def detect_agents(self, goal: str) -> list:

        goal_lower = goal.lower()
        agents = []

        if any(w in goal_lower for w in [
            "research", "market", "latest", "news",
            "trend", "current", "today", "2026",
            "update", "find", "search", "web"
        ]):
            agents.append("research")

        if any(w in goal_lower for w in [
            "memory", "remember", "history",
            "previous", "before", "last time"
        ]):
            agents.append("memory")

        if any(w in goal_lower for w in [
            "document", "pdf", "rag", "knowledge"
        ]):
            agents.append("rag")

        if any(w in goal_lower for w in [
            "website", "browser", "google",
            "open", "visit", "navigate"
        ]):
            agents.append("browser")

        return list(set(agents))

    # ==================================================
    # FALLBACK AGENT RUNNER
    # ==================================================

    async def run_agent_with_fallback(
        self,
        agent_name: str,
        goal: str,
        user_id: str = "default"
    ) -> dict:

        registry = get_registry()

        chain = [agent_name]
        if agent_name in registry:
            chain += registry[agent_name].get("fallbacks", [])

        seen = set()
        ordered_chain = []
        for name in chain:
            if name not in seen and name in registry:
                seen.add(name)
                ordered_chain.append(name)

        last_error = None

        for current_agent_name in ordered_chain:

            agent_entry = registry.get(current_agent_name)
            if not agent_entry:
                continue

            agent = agent_entry["agent"]

            try:

                await agent_bus.publish(
                    "orchestrator",
                    {
                        "event": "agent_started",
                        "agent": current_agent_name,
                        "goal": goal,
                        "is_fallback": current_agent_name != agent_name
                    }
                )

                import inspect
                sig = inspect.signature(agent.run)
                if "user_id" in sig.parameters:
                    result = await agent.run(
                        query=goal,
                        user_id=user_id
                    )
                else:
                    result = await agent.run(query=goal)

                if isinstance(result, dict) and not result.get("success", True):
                    raise Exception(
                        result.get("error", "Agent reported failure")
                    )

                learning_engine.record_success(current_agent_name)

                return {
                    "agent": current_agent_name,
                    "original_agent": agent_name,
                    "used_fallback": current_agent_name != agent_name,
                    "success": True,
                    "result": result
                }

            except Exception as e:

                last_error = str(e)
                learning_engine.record_failure(current_agent_name)
                print(
                    f"[FALLBACK] '{current_agent_name}' failed: {e}. "
                    f"Trying next..."
                )
                continue

        return {
            "agent": agent_name,
            "original_agent": agent_name,
            "used_fallback": True,
            "success": False,
            "result": None,
            "error": last_error
        }

    # ==================================================
    # EXECUTE ALL AGENTS CONCURRENTLY
    # ==================================================

    async def execute_agents(
        self,
        goal: str,
        user_id: str = "default"
    ) -> list:

        outputs = []
        selected_agents = self.detect_agents(goal)

        tasks = [
            self.run_agent_with_fallback(
                agent_name=name,
                goal=goal,
                user_id=user_id
            )
            for name in selected_agents
        ]

        if tasks:
            results = await asyncio.gather(
                *tasks,
                return_exceptions=True
            )
            for res in results:
                if isinstance(res, Exception):
                    continue
                outputs.append(res)

        return outputs

    # ==================================================
    # EXECUTE DYNAMIC SPECIALIZED AGENT
    # ==================================================

    async def execute_dynamic_agent(
        self,
        goal: str
    ) -> dict:

        detected = detect_specialized_agent(goal)

        if not detected:
            return {"agent": None, "status": "no_specialized_agent"}

        agent_name, specialty = detected
        agent = self.agent_factory.create_agent(agent_name, specialty)

        try:

            result = await agent.run(goal)

            score = learning_engine.evaluate_agent_output(
                agent_name, result
            )

            return {
                "agent": agent_name,
                "score": score,
                "success": True,
                "result": result
            }

        except Exception as e:

            learning_engine.record_failure(agent_name)

            return {
                "agent": agent_name,
                "success": False,
                "status": "failed",
                "error": str(e)
            }

    # ==================================================
    # MAIN EXECUTION
    # provider: "groq" | "gemini" | "openai" | None
    # ==================================================

    async def run(
        self,
        goal: str,
        user_id: str = "default",
        provider: str = None
    ):

        task_id = str(uuid.uuid4())

        await task_repository.create_task(
            task_id=task_id,
            user_id=user_id,
            goal=goal
        )

        try:

            # ------------------------------------------
            # STEP 1: Persistent memory context
            # ------------------------------------------
            memory_context = await self.memory.build_context_async(
                user_id=user_id,
                current_query=goal
            )

            # ------------------------------------------
            # STEP 2: RAG context
            # ------------------------------------------
            try:
                rag_context = self.rag.generate_context(
                    user_id=user_id,
                    query=goal
                )
            except Exception as e:
                rag_context = ""
                print(f"[RAG Error]: {e}")

            # ------------------------------------------
            # STEP 3: Plan
            # ------------------------------------------
            plan = create_plan(goal)

            # ------------------------------------------
            # STEP 4: Tool execution (web search etc.)
            # ------------------------------------------
            selected_tool = self.detect_tool(goal)
            tool_result = None
            web_search_context = ""

            if selected_tool:
                try:
                    tool_result = self.registry.execute(
                        selected_tool,
                        goal
                    )
                    # Extract formatted web results for LLM
                    if (
                        selected_tool == "web_search"
                        and isinstance(tool_result, dict)
                    ):
                        web_search_context = tool_result.get(
                            "formatted", ""
                        )
                except Exception as e:
                    print(f"[Tool Error]: {e}")

            # ------------------------------------------
            # STEP 5: Run all agents with fallback
            # ------------------------------------------
            agent_results = await self.execute_agents(
                goal, user_id
            )

            # ------------------------------------------
            # STEP 6: Dynamic specialized agent
            # ------------------------------------------
            dynamic_agent_result = await self.execute_dynamic_agent(
                goal
            )

            # ------------------------------------------
            # STEP 7: Critic evaluation
            # ------------------------------------------
            critic_result = await self.critic_agent.run(
                goal, agent_results
            )

            # ------------------------------------------
            # STEP 8: Build agent summary
            # ------------------------------------------
            agent_summary = ""
            for ar in agent_results:
                if ar.get("success") and ar.get("result"):
                    res = ar["result"]
                    # Use formatted_results if research agent
                    if isinstance(res, dict):
                        content = (
                            res.get("formatted_results")
                            or str(res)
                        )[:500]
                    else:
                        content = str(res)[:500]
                    agent_summary += f"\n[{ar['agent']}]:\n{content}\n"

            # ------------------------------------------
            # STEP 9: LLM synthesis with selected provider
            # Fallback chain handled inside ask_llm()
            # ------------------------------------------
            use_rag = (
                isinstance(rag_context, str)
                and len(rag_context.strip()) > 50
            )

            llm_prompt = f"""You are Nexora AI, an advanced AI agent platform built in 2026.

Conversation Memory (this user's previous chats):
{memory_context if memory_context else "No previous conversation."}

User Question:
{goal}

{f"Live Web Search Results:{chr(10)}{web_search_context}" if web_search_context else ""}

{f"Document Context:{chr(10)}{rag_context}" if use_rag else ""}

Agent Findings:
{agent_summary if agent_summary else "No additional agent findings."}

Dynamic Agent Result:
{str(dynamic_agent_result.get("result", ""))[:400]}

Critic Review:
{critic_result.get("feedback", "")}

Instructions:
- Answer the user's question directly, helpfully, and accurately.
- If web search results are provided, use them to give up-to-date 2026 information.
- Use conversation memory to personalize — remember the user's name and past topics.
- Be detailed, clear, and confident.
- Never say you don't have access to the internet if web results are provided above.
"""

            try:
                llm_response = await ask_llm(
                    llm_prompt,
                    provider=provider
                )
            except Exception as e:
                llm_response = (
                    "I'm having trouble generating a response. "
                    "Please try again in a moment."
                )
                print(f"[LLM Error]: {e}")

            # ------------------------------------------
            # STEP 10: Store to PostgreSQL permanently
            # ------------------------------------------
            await self.memory.store_memory_async(
                user_id=user_id,
                role="user",
                content=goal
            )

            await self.memory.store_memory_async(
                user_id=user_id,
                role="assistant",
                content=llm_response
            )

            # ------------------------------------------
            # STEP 11: Return full result
            # ------------------------------------------
            result = {
                "task_id": task_id,
                "final_answer": llm_response,
                "provider_used": provider or "groq (default)",
                "agent_leaderboard": learning_engine.get_agent_stats(),
                "best_agent": learning_engine.best_agent(),
                "goal": goal,
                "timestamp": str(datetime.utcnow()),
                "plan": plan,
                "memory_context": memory_context,
                "rag_context": rag_context,
                "web_search_context": web_search_context,
                "selected_tool": selected_tool,
                "tool_result": tool_result,
                "agents": agent_results,
                "dynamic_agent": dynamic_agent_result,
                "registered_dynamic_agents": self.agent_factory.list_agents(),
                "critic_review": critic_result
            }

            await task_repository.complete_task(task_id, result)

            return result

        except Exception as e:

            await task_repository.fail_task(task_id, str(e))
            raise e

    # ==================================================
    # TASK STATUS
    # ==================================================

    def get_best_agent(self):
        return learning_engine.best_agent()

    async def get_task_status(self, task_id: str):

        task = await task_repository.get_task(task_id)

        if not task:
            return {"status": "not_found"}

        return {
            "task_id": task.task_id,
            "user_id": task.user_id,
            "goal": task.goal,
            "status": task.status,
            "result": task.result,
            "error": task.error,
            "created_at": str(task.created_at),
            "completed_at": (
                str(task.completed_at)
                if task.completed_at else None
            )
        }


# ==================================================
# GLOBAL RUNNERS
# ==================================================

async def run_agent_async(
    user_goal: str,
    user_id: str = "default",
    provider: str = None
):
    orchestrator = AgentOrchestrator()
    return await orchestrator.run(
        goal=user_goal,
        user_id=user_id,
        provider=provider
    )


def run_agent(
    user_goal: str,
    user_id: str = "default",
    provider: str = None
):
    return asyncio.run(
        run_agent_async(
            user_goal=user_goal,
            user_id=user_id,
            provider=provider
        )
    )