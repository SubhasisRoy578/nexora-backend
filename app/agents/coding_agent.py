# ==================================================
# NEXORA AI — CODING AGENT
# Capabilities:
# - Generate code from natural language
# - Execute code in sandbox
# - Debug and fix broken code
# - Explain code
# - Refactor code
# ==================================================

import time
from datetime import datetime

from app.llm.llm_router import ask_llm
from app.tools.python_executor import execute_python


class CodingAgent:

    def __init__(self):
        self.name = "coding_agent"

    # ==================================================
    # DETECT INTENT
    # ==================================================

    def _detect_intent(self, query: str) -> str:
        """
        Detects what the user wants:
        generate | execute | debug | explain | refactor
        """

        q = query.lower()

        if any(w in q for w in [
            "debug", "fix", "error", "broken",
            "not working", "exception", "traceback"
        ]):
            return "debug"

        if any(w in q for w in [
            "explain", "what does", "how does",
            "understand", "walk me through"
        ]):
            return "explain"

        if any(w in q for w in [
            "refactor", "improve", "optimize",
            "clean up", "rewrite"
        ]):
            return "refactor"

        if any(w in q for w in [
            "run", "execute", "output of",
            "result of", "what happens if"
        ]):
            return "execute"

        return "generate"

    # ==================================================
    # EXTRACT CODE BLOCK FROM LLM RESPONSE
    # ==================================================

    def _extract_code(self, text: str) -> str:
        """
        Pulls code out of ```python ... ``` blocks.
        Falls back to full text if no block found.
        """

        if "```python" in text:
            start = text.find("```python") + 9
            end = text.find("```", start)
            if end != -1:
                return text[start:end].strip()

        if "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end != -1:
                return text[start:end].strip()

        return text.strip()

    # ==================================================
    # GENERATE CODE
    # ==================================================

    async def _generate_code(
        self,
        query: str,
        execute: bool = True
    ) -> dict:

        prompt = f"""You are an expert Python developer inside Nexora AI.

Task: {query}

Write clean, working Python code to solve this task.
- Use only standard library modules (math, random, json, datetime, etc.)
- Do NOT use os, sys, subprocess, requests, or file operations
- Add brief comments explaining key steps
- Make sure the code prints its output using print()

Return ONLY the Python code inside a ```python code block.
No explanation before or after.
"""

        raw = await ask_llm(prompt)
        code = self._extract_code(raw)

        result = {
            "intent": "generate",
            "code": code,
            "llm_response": raw,
        }

        if execute and code:
            exec_result = execute_python(code)
            result["execution"] = exec_result
            result["output"] = exec_result.get("output", "")
            result["execution_success"] = exec_result.get("success", False)

            # If execution failed, try auto-fix once
            if not exec_result.get("success") and not exec_result.get("blocked"):
                fixed = await self._auto_fix(
                    code,
                    exec_result.get("error", "")
                )
                result["auto_fix"] = fixed

        return result

    # ==================================================
    # AUTO FIX
    # ==================================================

    async def _auto_fix(
        self,
        code: str,
        error: str
    ) -> dict:

        prompt = f"""You are an expert Python debugger inside Nexora AI.

The following Python code produced an error:

```python
{code}
```

Error:
{error}

Fix the code so it runs correctly.
- Keep the same logic and goal
- Do NOT use os, sys, subprocess, requests, or file operations
- Make sure print() is used for output

Return ONLY the fixed Python code inside a ```python code block.
"""

        raw = await ask_llm(prompt)
        fixed_code = self._extract_code(raw)

        exec_result = execute_python(fixed_code)

        return {
            "fixed_code": fixed_code,
            "execution": exec_result,
            "output": exec_result.get("output", ""),
            "success": exec_result.get("success", False)
        }

    # ==================================================
    # DEBUG CODE
    # ==================================================

    async def _debug_code(
        self,
        query: str
    ) -> dict:

        prompt = f"""You are an expert Python debugger inside Nexora AI.

User request: {query}

1. Identify the bug or issue described
2. Explain what is wrong in 1-2 sentences
3. Provide the fixed code

Return in this format:
DIAGNOSIS: <what is wrong>
```python
<fixed code here>
```
"""

        raw = await ask_llm(prompt)
        fixed_code = self._extract_code(raw)

        diagnosis = ""
        for line in raw.splitlines():
            if line.startswith("DIAGNOSIS:"):
                diagnosis = line.replace("DIAGNOSIS:", "").strip()
                break

        exec_result = execute_python(fixed_code) if fixed_code else {}

        return {
            "intent": "debug",
            "diagnosis": diagnosis,
            "fixed_code": fixed_code,
            "execution": exec_result,
            "output": exec_result.get("output", ""),
            "execution_success": exec_result.get("success", False),
            "llm_response": raw
        }

    # ==================================================
    # EXPLAIN CODE
    # ==================================================

    async def _explain_code(
        self,
        query: str
    ) -> dict:

        prompt = f"""You are an expert Python teacher inside Nexora AI.

User request: {query}

Explain the code clearly:
- What it does overall
- What each major section does
- Any important patterns or concepts used
- Potential improvements

Be clear, concise, and educational.
"""

        explanation = await ask_llm(prompt)

        return {
            "intent": "explain",
            "explanation": explanation,
            "llm_response": explanation
        }

    # ==================================================
    # REFACTOR CODE
    # ==================================================

    async def _refactor_code(
        self,
        query: str
    ) -> dict:

        prompt = f"""You are an expert Python engineer inside Nexora AI.

User request: {query}

Refactor the code:
- Improve readability and structure
- Follow PEP 8 style
- Optimize where possible
- Add docstrings if missing
- Do NOT change the core logic

Return ONLY the refactored code inside a ```python code block.
Then add a brief CHANGES: section explaining what you improved.
"""

        raw = await ask_llm(prompt)
        refactored_code = self._extract_code(raw)

        changes = ""
        if "CHANGES:" in raw:
            changes = raw[raw.find("CHANGES:"):].replace("CHANGES:", "").strip()

        exec_result = execute_python(refactored_code) if refactored_code else {}

        return {
            "intent": "refactor",
            "refactored_code": refactored_code,
            "changes": changes,
            "execution": exec_result,
            "output": exec_result.get("output", ""),
            "execution_success": exec_result.get("success", False),
            "llm_response": raw
        }

    # ==================================================
    # MAIN RUN METHOD
    # ==================================================

    async def run(
        self,
        query: str,
        user_id: str = "default"
    ) -> dict:

        start_time = time.time()

        try:

            intent = self._detect_intent(query)

            if intent == "debug":
                result = await self._debug_code(query)

            elif intent == "explain":
                result = await self._explain_code(query)

            elif intent == "refactor":
                result = await self._refactor_code(query)

            elif intent == "execute":
                result = await self._generate_code(
                    query,
                    execute=True
                )

            else:
                # Default: generate + execute
                result = await self._generate_code(
                    query,
                    execute=True
                )

            execution_time = round(
                time.time() - start_time, 2
            )

            return {
                "agent": "coding_agent",
                "success": True,
                "query": query,
                "intent": intent,
                "timestamp": str(datetime.utcnow()),
                "execution_time": execution_time,
                **result
            }

        except Exception as e:

            return {
                "agent": "coding_agent",
                "success": False,
                "query": query,
                "error": str(e),
                "timestamp": str(datetime.utcnow()),
                "execution_time": round(time.time() - start_time, 2)
            }