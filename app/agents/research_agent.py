# ==================================================
# NEXORA AI — RESEARCH AGENT
# Uses DuckDuckGo with 2026 freshness injection.
# Returns structured results for LLM synthesis.
# ==================================================

from datetime import datetime
import time

from app.tools.web_search import search_web, format_search_results


class ResearchAgent:

    async def run(
        self,
        query: str
    ):

        start_time = time.time()

        try:

            results = search_web(query)

            summary = []

            if results:

                for item in results[:6]:

                    title = item.get("title", "")
                    body = item.get("body", "")
                    url = item.get("href", "")

                    summary.append({
                        "title": title,
                        "summary": body[:300],
                        "source": url
                    })

            formatted = format_search_results(results)

            execution_time = round(
                time.time() - start_time, 2
            )

            return {
                "agent": "research_agent",
                "success": True,
                "query": query,
                "results_found": len(results),
                "summary": summary,
                "formatted_results": formatted,
                "results": results,
                "timestamp": str(datetime.utcnow()),
                "execution_time": execution_time,
                "top_result": results[0] if results else None,
                "confidence": min(len(results) * 15, 100),
                "research_status": "completed"
            }

        except Exception as e:

            return {
                "agent": "research_agent",
                "success": False,
                "query": query,
                "results_found": 0,
                "summary": [],
                "results": [],
                "error": str(e),
                "research_status": "failed"
            }