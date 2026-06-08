# ==================================================
# NEXORA AI — TOOL REGISTRY
# Fixed: web_search_tool now actually calls search_web()
# ==================================================

from app.tools.calculator import calculate
from app.tools.file_reader import read_pdf
from app.tools.python_executor import execute_python
from app.tools.web_search import search_web, format_search_results
from app.tools.browser_tools import open_website, search_google


class ToolRegistry:

    def __init__(self):

        self.tools = {
            "calculator":     self.calculator_tool,
            "file_reader":    self.file_reader_tool,
            "web_search":     self.web_search_tool,
            "python_executor": self.python_executor_tool,
            "open_website":   self.open_website_tool,
            "google_search":  self.google_search_tool,
        }

    def calculator_tool(self, expression):
        return calculate(expression)

    def file_reader_tool(self, path):
        return read_pdf(path)

    def web_search_tool(self, query):
        """
        Fixed: was returning a stub dict.
        Now actually calls search_web() and
        formats results as a string for LLM.
        """
        try:
            results = search_web(query)
            return {
                "tool": "web_search",
                "query": query,
                "results": results,
                "formatted": format_search_results(results),
                "count": len(results)
            }
        except Exception as e:
            return {
                "tool": "web_search",
                "query": query,
                "results": [],
                "formatted": "",
                "error": str(e)
            }

    def python_executor_tool(self, code):
        return execute_python(code)

    def open_website_tool(self, url):
        return open_website(url)

    def google_search_tool(self, query):
        return search_google(query)

    def execute(self, tool_name, input_data):

        tool = self.tools.get(tool_name)

        if not tool:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found"
            }

        try:
            return tool(input_data)
        except Exception as e:
            return {
                "success": False,
                "tool": tool_name,
                "error": str(e)
            }