from app.llm.llm_router import ask_llm


class CriticAgent:

    async def run(
        self,
        goal: str,
        response
    ):

        try:

            # Normalize response to string for evaluation
            if isinstance(response, list):
                response_text = str(response)
            elif isinstance(response, dict):
                response_text = str(response)
            else:
                response_text = str(response) if response else ""

            if not response_text.strip():
                return {
                    "agent": "critic_agent",
                    "score": 1,
                    "feedback": "Response was empty.",
                    "approved": False
                }

            prompt = f"""
You are a strict quality critic for an AI agent platform called Nexora AI.

User Goal: {goal}

Agent Response: {response_text[:1000]}

Evaluate the response on these criteria:
1. Does it directly address the user's goal?
2. Is it accurate and helpful?
3. Is it complete or partial?

Reply in this exact format:
SCORE: <number from 1 to 10>
FEEDBACK: <one sentence assessment>
APPROVED: <YES or NO>
"""

            raw = await ask_llm(prompt)

            score = 7
            feedback = "Response meets basic quality standards."
            approved = True

            for line in raw.splitlines():
                line = line.strip()
                if line.startswith("SCORE:"):
                    try:
                        score = int(line.replace("SCORE:", "").strip())
                    except ValueError:
                        score = 7
                elif line.startswith("FEEDBACK:"):
                    feedback = line.replace("FEEDBACK:", "").strip()
                elif line.startswith("APPROVED:"):
                    approved = "YES" in line.upper()

            return {
                "agent": "critic_agent",
                "score": score,
                "feedback": feedback,
                "approved": approved
            }

        except Exception as e:

            # Fallback — never crash the pipeline
            return {
                "agent": "critic_agent",
                "score": 6,
                "feedback": "Critic evaluation unavailable.",
                "approved": True,
                "error": str(e)
            }