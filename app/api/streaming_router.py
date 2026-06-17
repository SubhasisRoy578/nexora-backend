# ==================================================
# NEXORA AI — STREAMING ROUTER
# Provides two streaming endpoints:
# 1. POST /stream/chat  → Server-Sent Events (SSE)
# 2. WS   /ws/chat      → WebSocket
# Both stream LLM tokens word-by-word like ChatGPT.
# ==================================================

import asyncio
import json
from typing import Optional, AsyncIterator

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.memory.memory_manager import MemoryManager
from app.llm.llm_router import stream_llm
from app.agents.orchestrator import AgentOrchestrator

router = APIRouter()

memory_manager = MemoryManager()
orchestrator = AgentOrchestrator()


# ==================================================
# REQUEST MODEL (SSE)
# ==================================================

class StreamRequest(BaseModel):
    user_id: str
    message: str
    provider: Optional[str] = None


# ==================================================
# SHARED: Build LLM prompt with memory + context
# ==================================================

async def build_prompt(
    user_id: str,
    message: str
) -> str:

    memory_context = await memory_manager.build_context_async(
        user_id=user_id,
        current_query=message
    )

    prompt = f"""You are Nexora AI, an advanced AI agent platform.

Conversation Memory:
{memory_context if memory_context else "No previous conversation."}

User Question:
{message}

Instructions:
- Answer directly and helpfully.
- Use conversation memory to personalize your response.
- Be detailed, accurate, and clear.
"""

    return prompt


# ==================================================
# SHARED: Store turn to memory after streaming done
# ==================================================

async def store_turn(
    user_id: str,
    message: str,
    response: str
):

    try:
        await memory_manager.store_memory_async(
            user_id=user_id,
            role="user",
            content=message
        )
        await memory_manager.store_memory_async(
            user_id=user_id,
            role="assistant",
            content=response
        )
    except Exception as e:
        print(f"[Streaming] Memory store error: {e}")


# ==================================================
# SSE ENDPOINT
# POST /stream/chat
# Frontend reads response as EventSource stream.
# Each chunk: "data: <token>\n\n"
# Final chunk: "data: [DONE]\n\n"
# ==================================================

async def sse_generator(
    user_id: str,
    message: str,
    provider: Optional[str]
) -> AsyncIterator[str]:

    full_response = ""

    try:

        prompt = await build_prompt(user_id, message)

        # Send start signal
        yield f"data: {json.dumps({'type': 'start'})}\n\n"

        async for token in stream_llm(
            prompt=prompt,
            provider=provider
        ):
            full_response += token

            yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

            # Small delay to prevent overwhelming the client
            await asyncio.sleep(0)

        # Send done signal
        yield f"data: {json.dumps({'type': 'done', 'full_response': full_response})}\n\n"

    except Exception as e:

        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    finally:

        # Store full conversation to memory
        if full_response:
            await store_turn(user_id, message, full_response)


@router.post("/stream/chat")
async def stream_chat(request: StreamRequest):
    """
    Server-Sent Events streaming endpoint.
    Use with EventSource on the frontend.

    Example frontend usage:
        const response = await fetch('/stream/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id, message, provider })
        });
        const reader = response.body.getReader();
    """

    return StreamingResponse(
        sse_generator(
            user_id=request.user_id,
            message=request.message,
            provider=request.provider
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
    )


# ==================================================
# WEBSOCKET ENDPOINT
# WS /ws/chat
# Frontend connects once, sends messages, receives
# streamed tokens in real-time.
# Message format IN:  {"user_id": "...", "message": "...", "provider": "..."}
# Message format OUT: {"type": "token"|"done"|"error", "content": "..."}
# ==================================================

@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket streaming endpoint.
    Persistent connection — user can send multiple
    messages without reconnecting.

    Example frontend usage:
        const ws = new WebSocket('ws://localhost:8000/ws/chat');
        ws.send(JSON.stringify({ user_id, message }));
        ws.onmessage = (e) => {
            const data = JSON.parse(e.data);
            if (data.type === 'token') appendText(data.content);
        };
    """

    await websocket.accept()

    print("[WebSocket] Client connected")

    try:

        while True:

            # Wait for message from client
            raw = await websocket.receive_text()

            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON"
                }))
                continue

            user_id = payload.get("user_id", "default")
            message = payload.get("message", "")
            provider = payload.get("provider", None)

            if not message.strip():
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Empty message"
                }))
                continue

            # Send typing indicator
            await websocket.send_text(json.dumps({
                "type": "start",
                "user_id": user_id
            }))

            full_response = ""

            try:

                prompt = await build_prompt(user_id, message)

                async for token in stream_llm(
                    prompt=prompt,
                    provider=provider
                ):
                    full_response += token

                    await websocket.send_text(json.dumps({
                        "type": "token",
                        "content": token
                    }))

                    await asyncio.sleep(0)

                # Send completion signal
                await websocket.send_text(json.dumps({
                    "type": "done",
                    "full_response": full_response
                }))

                # Store to persistent memory
                await store_turn(user_id, message, full_response)

            except Exception as e:

                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": str(e)
                }))

    except WebSocketDisconnect:
        print("[WebSocket] Client disconnected")

    except Exception as e:
        print(f"[WebSocket] Unexpected error: {e}")
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Connection error"
            }))
        except Exception:
            pass