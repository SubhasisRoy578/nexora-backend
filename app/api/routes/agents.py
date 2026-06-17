
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from typing import List
import uuid

from server.database import get_postgres_db
from server.models.agent import AgentRun, AgentRunStatus, AgentTool
from server.models.user import User
from server.schemas.schemas import AgentRunRequest, AgentRunResponse, AgentRunListResponse
from server.services.agents.agent_orchestrator import orchestrator, crew_system
from server.middleware.auth_middleware import get_current_user, require_subscription

router = APIRouter()


@router.post("/run/stream")
async def run_agent_stream(
    payload: AgentRunRequest,
    current_user: User = Depends(require_subscription("free")),
    db: AsyncSession = Depends(get_postgres_db),
):
    """
    Run a single AI agent and stream its reasoning steps back via SSE.
    The agent can use tools: web_search, calculator, code_interpreter.
    """
    run_id = str(uuid.uuid4())

    # Create run record
    run = AgentRun(
        id=uuid.UUID(run_id),
        user_id=current_user.id,
        session_id=payload.session_id,
        task_description=payload.task,
        agent_type=payload.agent_type,
        status=AgentRunStatus.RUNNING,
        tools_used=payload.tools or [],
        started_at=datetime.utcnow(),
    )
    db.add(run)
    await db.commit()

    async def stream_generator():
        import json
        steps = []
        tokens_used = 0
        start = datetime.utcnow()

        try:
            async for event in orchestrator.run_agent(
                task=payload.task,
                user_id=str(current_user.id),
                tool_names=payload.tools,
                stream=True,
            ):
                yield event

            # Update run status
            duration = (datetime.utcnow() - start).total_seconds()
            run.status = AgentRunStatus.COMPLETED
            run.completed_at = datetime.utcnow()
            run.duration_seconds = duration
            await db.commit()

        except Exception as e:
            run.status = AgentRunStatus.FAILED
            run.error_message = str(e)[:500]
            await db.commit()
            error_data = json.dumps({"error": str(e)})
            yield f"event: error\ndata: {error_data}\n\n"

    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Agent-Run-ID": run_id,
        },
    )


@router.post("/crew/run")
async def run_crew_agent(
    payload: AgentRunRequest,
    current_user: User = Depends(require_subscription("pro")),
    db: AsyncSession = Depends(get_postgres_db),
):
    """
    Run a multi-agent CrewAI workflow (Researcher + Writer + Critic).
    Requires Pro subscription. Returns result after completion.
    """
    run_id = str(uuid.uuid4())
    start = datetime.utcnow()

    run = AgentRun(
        id=uuid.UUID(run_id),
        user_id=current_user.id,
        task_description=payload.task,
        agent_type="crew",
        status=AgentRunStatus.RUNNING,
        started_at=start,
    )
    db.add(run)
    await db.commit()

    try:
        result = await crew_system.run_crew(topic=payload.task)
        duration = (datetime.utcnow() - start).total_seconds()

        run.status = AgentRunStatus.COMPLETED
        run.result = result[:10000]  # Cap stored result
        run.completed_at = datetime.utcnow()
        run.duration_seconds = duration
        await db.commit()

        return {
            "run_id": run_id,
            "status": "completed",
            "result": result,
            "duration_seconds": duration,
        }

    except Exception as e:
        run.status = AgentRunStatus.FAILED
        run.error_message = str(e)[:500]
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Agent run failed: {e}")


@router.get("/runs", response_model=AgentRunListResponse)
async def list_agent_runs(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_postgres_db),
):
    """Get all past agent runs for the current user."""
    from sqlalchemy import func

    result = await db.execute(
        select(AgentRun)
        .where(AgentRun.user_id == current_user.id)
        .order_by(AgentRun.created_at.desc())
        .offset(offset).limit(limit)
    )
    runs = result.scalars().all()

    count_result = await db.execute(
        select(func.count(AgentRun.id)).where(AgentRun.user_id == current_user.id)
    )
    total = count_result.scalar()

    return {"runs": runs, "total": total}


@router.get("/runs/{run_id}", response_model=AgentRunResponse)
async def get_agent_run(
    run_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_postgres_db),
):
    """Get details of a specific agent run."""
    result = await db.execute(
        select(AgentRun).where(
            AgentRun.id == uuid.UUID(run_id),
            AgentRun.user_id == current_user.id,
        )
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")
    return run


@router.get("/tools")
async def list_tools(current_user: User = Depends(get_current_user)):
    """List all available agent tools."""
    return {
        "tools": [
            {
                "name": "web_search",
                "description": "Search the internet for current information",
                "category": "search",
                "requires_auth": False,
            },
            {
                "name": "calculator",
                "description": "Perform mathematical calculations",
                "category": "computation",
                "requires_auth": False,
            },
            {
                "name": "code_interpreter",
                "description": "Execute Python code and return output",
                "category": "computation",
                "requires_auth": False,
            },
            {
                "name": "file_reader",
                "description": "Read and analyze uploaded files",
                "category": "files",
                "requires_auth": False,
            },
            {
                "name": "gmail",
                "description": "Read and send emails via Gmail",
                "category": "connector",
                "requires_auth": True,
            },
            {
                "name": "notion",
                "description": "Read and write Notion pages",
                "category": "connector",
                "requires_auth": True,
            },
        ]
    }