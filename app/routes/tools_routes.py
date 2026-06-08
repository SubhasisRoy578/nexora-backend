from fastapi import APIRouter
from pydantic import BaseModel

from app.tools.tool_registry import ToolRegistry

router = APIRouter()

registry = ToolRegistry()


class ToolRequest(BaseModel):
    tool_name: str
    input_data: str


@router.post("/execute")
async def execute_tool(request: ToolRequest):

    result = registry.execute(
        request.tool_name,
        request.input_data
    )

    return {
        "tool": request.tool_name,
        "result": result
    }