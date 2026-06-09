from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from app.routes.pdf_routes import (
    router as pdf_router
)
load_dotenv()
from app.api.file_routes import router as file_router
from app.routes.learning_routes import (
    router as learning_router
)
from pathlib import Path
from app.api.streaming_router import router as streaming_router
from app.routes.distributed_tasks import (
    router as distributed_router
)
from app.database.models import AgentTask
from app.workers.worker_manager import (
    worker_manager
)
from app.routes.websocket_routes import router as websocket_router
from app.routes.tools_routes import router as tools_router
from app.routes.autonomous_routes import (
    router as autonomous_router
)

from app.routes.task_status_routes import (
    router as task_status_router
)
from app.routes.stream_routes import router as stream_router
# =========================
# DATABASE
# =========================

from app.database.database import engine, Base

# =========================
# EXISTING FEATURES
# =========================

from app.chat_routes import router as chat_router

# =========================
# UPLOAD + FILE SYSTEM
# =========================

from app.routes.upload_routes import router as upload_router

# =========================
# RAG SYSTEM
# =========================

from app.routes.rag_routes import router as rag_router

# =========================
# MEMORY SYSTEM
# =========================

from app.routes.memory_routes import router as memory_router

# =========================
# AUTH
# =========================

from app.routes.auth_routes import router as auth_router

# =========================
# AGENT WORKFLOWS
# =========================

from app.routes.agent_routes import router as agent_router

# =========================
# TASK EXECUTION
# =========================

from app.routes.task_routes import router as task_router

# =========================
# BROWSER AUTOMATION
# =========================

from app.routes.browser_routes import router as browser_router

# =========================
# ANALYTICS
# =========================

from app.routes.analytics_routes import router as analytics_router

# =========================
# VECTOR MEMORY
# =========================

from app.routes.vector_routes import router as vector_router

# =========================
# SETTINGS
# =========================

from app.routes.settings_routes import router as settings_router


# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(
    title="Nexora AI",
    version="10.0.0",
    description="Enterprise-grade AI Agent Platform"
)

# =========================================================
# STATIC FILES
# =========================================================

app.mount("/static", StaticFiles(directory="app/static"), name="static")

# =========================================================
# FRONTEND
# =========================================================

FRONTEND_PATH = Path("app/static/index.html")


@app.get("/")
async def frontend():
    return FileResponse(FRONTEND_PATH)

# =========================================================
# DATABASE INITIALIZATION
# =========================================================

@app.on_event("startup")
async def startup():

    async with engine.begin() as conn:

        await conn.run_sync(
            Base.metadata.create_all
        )

    await worker_manager.start()

# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
# ROUTERS
# =========================================================

# CHAT
app.include_router(
    stream_router,
    prefix="/api",
    tags=["Streaming & Agents"]
)

app.include_router(
    chat_router,
    prefix="/api/chat",
    tags=["Chat"]
)

app.include_router(
    autonomous_router,
    prefix="/api/autonomous",
    tags=["Autonomous AI"]
)

app.include_router(
    tools_router,
    prefix="/api/tools",
    tags=["Tools"]
)

app.include_router(
    upload_router,
    prefix="/api/upload",
    tags=["Upload"]
)

app.include_router(
    learning_router
)

app.include_router(
    pdf_router,
    prefix="/pdf",
    tags=["PDF"]
)

app.include_router(
    task_status_router,
    prefix="/api/task-status",
    tags=["Task Status"]
)
# RAG
app.include_router(
    rag_router,
    prefix="/api/rag",
    tags=["RAG"]
)

# MEMORY
app.include_router(
    memory_router,
    prefix="/api/memory",
    tags=["Memory"]
)

# AUTH
app.include_router(
    auth_router,
    prefix="/api/auth",
    tags=["Auth"]
)

# AGENTS
app.include_router(
    agent_router,
    prefix="/api/agents",
    tags=["Agents"]
)

# TASKS
app.include_router(
    task_router,
    prefix="/api/tasks",
    tags=["Tasks"]
)

# BROWSER AUTOMATION
app.include_router(
    browser_router,
    prefix="/api/browser",
    tags=["Browser"]
)

# ANALYTICS
app.include_router(
    analytics_router,
    prefix="/api/analytics",
    tags=["Analytics"]
)

# VECTOR MEMORY
app.include_router(
    vector_router,
    prefix="/api/vector",
    tags=["Vector"]
)

# SETTINGS
app.include_router(
    settings_router,
    prefix="/api/settings",
    tags=["Settings"]
)

app.include_router(
    file_router, 
    prefix="/api/files", 
    tags=["Files"]
)

app.include_router(
    distributed_router,
    prefix="/api/distributed",
    tags=["Distributed Tasks"]
)

app.include_router(streaming_router)

app.include_router(
    websocket_router,
    prefix="/api",
    tags=["WebSocket"]
)
@app.get("/health")
async def health():
    return {
        "status": "healthy"
    }

# =========================================================
# SYSTEM INFO
# =========================================================
@app.get("/capabilities")
async def capabilities():

    return {

    "chat": True,

    "streaming": True,

    "memory": True,

    "vector_memory": True,

    "rag": True,

    "multi_agent": True,

    "tool_calling": True,

    "task_queue": True,

    "browser_automation": True,

    "analytics": True,

    "pdf_upload": True,

    "pdf_analysis": True,

    "pdf_qa": True,

    "llm_integration": True
}
@app.get("/system")
async def system_info():
    return {
        "status": "running",
        "project": "Nexora AI",
        "version": "10.0.0",

        "features": {

            "chat": True,
            "persistent_memory": True,
            "semantic_memory": True,
            "episodic_memory": True,

            "rag": True,
            "document_intelligence": True,
            "ocr": True,

            "large_file_uploads": True,
            "cloud_ready_storage": True,
            "drag_drop_uploads": True,

            "browser_automation": True,
            "multi_agent_workflows": True,
            "task_execution_chains": True,

            "vector_database": True,
            "semantic_retrieval": True,

            "google_auth": True,
            "production_backend": True
        }
    }
