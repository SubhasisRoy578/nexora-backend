from app.browser.google_search import google_search


class BrowserAgent:

    async def run(self, query: str):

        try:

            results = await google_search(query)

            return {
                "agent": "browser_agent",
                "success": True,
                "results": results
            }

        except Exception as e:

            return {
                "agent": "browser_agent",
                "success": False,
                "error": str(e)
            }