from app.browser.google_search import (
    google_search
)

from app.browser.website_reader import (
    read_website
)

from app.browser.browser_memory import (
    save_browser_memory
)

from app.browser.action_history import (
    save_action
)

async def run_browser_agent(
    task: str
):

    if "search" in task.lower():

        query = task.replace(
            "search",
            ""
        )

        results = await google_search(
            query
        )

        save_browser_memory(
            task,
            results
        )

        save_action(task)

        return {
            "type": "search",
            "results": results
        }

    elif "read" in task.lower():

        words = task.split()

        url = words[-1]

        content = await read_website(
            url
        )

        save_browser_memory(
            task,
            content
        )

        save_action(task)

        return {
            "type": "website",
            "content": content
        }

    return {
        "message": "Unsupported task"
    }