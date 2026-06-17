from tavily import TavilyClient
import os
from dotenv import load_dotenv

load_dotenv()

client = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY")
)

async def search_web(query: str):

    response = client.search(
        query=query,
        search_depth="advanced",
        max_results=3
    )

    print("TAVILY RESPONSE:")
    print(response)

    results = response.get("results", [])

    formatted_results = ""

    for item in results:

        formatted_results += f"""
Title: {item.get('title')}

Content: {item.get('content')}

URL: {item.get('url')}

-------------------
"""

    return formatted_results