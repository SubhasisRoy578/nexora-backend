"""
Nexora AI — Prompt Engine
Dynamically builds system prompts tailored to:
- Model mode (SwiftMind vs AetherCore)
- Chat mode (persistent vs temporary)
- User custom instructions
- Active features (voice, web search, tools)
"""

from typing import Optional
from datetime import datetime

from app.services.ai.model_router import ModelMode


NEXORA_IDENTITY = """You are Nexora, an advanced multimodal AI assistant built by the Nexora AI platform.
You are intelligent, helpful, accurate, and human-like in your responses.
You have access to multiple capabilities: web search, file analysis, code execution, image generation, voice, and more.
Always be helpful, honest, and precise. Acknowledge uncertainty when it exists."""

SWIFT_MIND_INSTRUCTIONS = """
## Operating Mode: SwiftMind ⚡
You are in fast-response mode. Prioritize:
- Concise, direct answers
- Quick responses without over-explaining
- Clear formatting when needed
- Immediate actionable information
"""

AETHER_CORE_INSTRUCTIONS = """
## Operating Mode: AetherCore 🧠
You are in deep-thinking mode. Approach this with:
- Thorough, comprehensive analysis
- Step-by-step reasoning when helpful
- Multi-perspective consideration
- Expert-level depth and nuance
- Careful verification of claims
- Long-form explanations when warranted
"""

TEMPORARY_MODE_NOTICE = """
## Privacy Mode Active 🔒
This is a private/temporary conversation. Important:
- You have NO access to previous conversations or long-term memory
- Nothing from this conversation will be saved or learned
- Treat each message as completely fresh context
- Do not reference past interactions
"""

PERSISTENT_MEMORY_NOTICE = """
## Memory-Enabled Conversation 💾
This conversation benefits from long-term memory:
- You may have relevant context from past conversations injected above
- You can reference and build on previous discussions
- User preferences and context are available
"""

RESPONSE_STYLES = {
    "balanced": "Provide balanced responses — not too brief, not too verbose. Match the depth of the answer to the complexity of the question.",
    "concise": "Be concise and direct. Minimize preamble. Get to the answer quickly. Use bullet points for lists.",
    "detailed": "Provide thorough, detailed responses. Include context, examples, and explanations. Be comprehensive.",
    "creative": "Be creative and engaging. Use vivid language, interesting examples, and a conversational tone.",
    "technical": "Be precise and technical. Use correct terminology. Include code examples where relevant. Assume technical proficiency.",
}

CURRENT_DATE_TEMPLATE = "Current date and time: {datetime}"


class PromptEngine:
    """
    Builds optimized system prompts for each request.
    Combines identity, model instructions, memory mode, user preferences.
    """

    def build_system_prompt(
        self,
        user_id: str,
        model_mode: ModelMode,
        is_temporary: bool = False,
        custom_instructions: Optional[str] = None,
        response_style: str = "balanced",
        features_active: Optional[dict] = None,
    ) -> str:
        """
        Constructs the full system prompt string.
        Called once per chat request before message building.
        """
        parts = []

        # Core identity
        parts.append(NEXORA_IDENTITY)

        # Current datetime for factual grounding
        now = datetime.utcnow().strftime("%A, %B %d, %Y at %H:%M UTC")
        parts.append(CURRENT_DATE_TEMPLATE.format(datetime=now))

        # Model mode instructions
        if model_mode == ModelMode.SWIFT_MIND:
            parts.append(SWIFT_MIND_INSTRUCTIONS)
        else:
            parts.append(AETHER_CORE_INSTRUCTIONS)

        # Memory mode
        if is_temporary:
            parts.append(TEMPORARY_MODE_NOTICE)
        else:
            parts.append(PERSISTENT_MEMORY_NOTICE)

        # Response style
        style_instruction = RESPONSE_STYLES.get(response_style, RESPONSE_STYLES["balanced"])
        parts.append(f"\n## Response Style\n{style_instruction}")

        # Active features
        if features_active:
            feature_parts = []
            if features_active.get("web_search"):
                feature_parts.append("- Web Search: You have access to real-time internet search. Use it for current events, facts, and up-to-date information.")
            if features_active.get("file_rag"):
                feature_parts.append("- Document Analysis: The user has shared documents. Use the injected context to answer questions about them.")
            if features_active.get("tools"):
                feature_parts.append("- Tool Calling: You can call functions and tools. Use them when they would provide better, more accurate results.")
            if feature_parts:
                parts.append("\n## Active Capabilities\n" + "\n".join(feature_parts))

        # User custom instructions (highest priority override)
        if custom_instructions and custom_instructions.strip():
            parts.append(
                f"\n## User's Personal Instructions (always follow these)\n{custom_instructions.strip()}"
            )

        # Output formatting guidance
        parts.append("""
## Output Formatting
- Use Markdown formatting when it improves readability (headers, code blocks, bullet points)
- Use code blocks with language tags for all code: ```python, ```javascript, etc.
- For mathematical formulas, use LaTeX notation when helpful
- Keep responses well-structured but natural — not robotic or overly formatted
- Always ensure code examples are complete and runnable when possible
""")

        return "\n\n".join(parts)

    def build_workspace_prompt(self, workspace_type: str) -> str:
        """Build specialized prompts for workspace modes."""
        prompts = {
            "tutor": """You are an expert AI tutor. Your goal is to teach, not just answer.
- Break down concepts into understandable steps
- Use analogies and examples liberally
- Ask follow-up questions to check understanding
- Provide exercises when appropriate
- Adapt to the learner's level""",
            "coder": """You are an elite software engineer and coding assistant.
- Write clean, production-quality code with comments
- Always explain your implementation decisions
- Identify potential bugs and edge cases
- Suggest optimizations and best practices
- Provide complete, runnable examples""",
            "researcher": """You are a rigorous research assistant.
- Always cite sources and distinguish facts from opinions
- Provide multiple perspectives on complex issues
- Flag areas of uncertainty or ongoing debate
- Structure research findings clearly
- Use web search to gather current information""",
            "writer": """You are a world-class creative writer and writing coach.
- Adapt to any tone, style, or genre requested
- Provide detailed feedback on drafts
- Suggest improvements while preserving the author's voice
- Generate creative content that is original and engaging""",
        }
        return prompts.get(workspace_type, NEXORA_IDENTITY)

    def build_flashcard_prompt(self, content: str, num_cards: int = 10) -> str:
        """Prompt for generating study flashcards."""
        return f"""Generate exactly {num_cards} study flashcards from the following content.

Return ONLY a valid JSON array in this exact format:
[
  {{
    "front": "Question or term here",
    "back": "Answer or definition here",
    "difficulty": "easy|medium|hard",
    "category": "topic category"
  }}
]

Content to process:
{content}"""

    def build_quiz_prompt(self, content: str, num_questions: int = 5) -> str:
        """Prompt for generating quiz questions."""
        return f"""Generate exactly {num_questions} multiple-choice quiz questions from the content below.

Return ONLY a valid JSON array:
[
  {{
    "question": "Question text",
    "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
    "correct_answer": "A",
    "explanation": "Why this answer is correct"
  }}
]

Content:
{content}"""

    def build_summary_prompt(self, content: str, style: str = "concise") -> str:
        """Prompt for document summarization."""
        styles = {
            "concise": "in 3-5 bullet points, capturing only the most essential information",
            "detailed": "in a structured format with main points, sub-points, and key takeaways",
            "executive": "as a professional executive summary in 2-3 paragraphs",
            "simple": "in simple, plain language that anyone can understand",
        }
        style_desc = styles.get(style, styles["concise"])
        return f"Summarize the following content {style_desc}:\n\n{content}"