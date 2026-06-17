from fastapi import APIRouter
from pydantic import BaseModel
import os

from langchain_groq import ChatGroq

from app.chat.streaming_chat import StreamingChatEngine
from app.agents.orchestrator import (
    run_agent_async
)

router = APIRouter()

GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY"
)

llm = ChatGroq(
    model="llama3-70b-8192",
    api_key=GROQ_API_KEY
)

stream_engine = StreamingChatEngine(
    llm
)


class StreamRequest(BaseModel):
    message: str


class AgentRequest(BaseModel):
    user_id: str
    goal: str


@router.post("/stream")
async def stream_chat(
    request: StreamRequest
):

    return await stream_engine.stream_response(
        request.message
    )


@router.post("/chat")
async def normal_chat(
    request: StreamRequest
):

    return await stream_engine.normal_response(
        request.message
    )


@router.post("/agents/run")
async def execute_agents(
    request: AgentRequest
):

    return await run_agent_async(
    user_goal=request.goal,
    user_id=request.user_id
)