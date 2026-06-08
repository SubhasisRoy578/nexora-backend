from fastapi import APIRouter

from app.browser.browser_agent import (
    run_browser_agent
)

router = APIRouter()

@router.post("/browser")

async def browser_task(data: dict):

    task = data.get("task")

    result = await run_browser_agent(task)

    return result