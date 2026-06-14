from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv()

# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(
    title="Nexora AI",
    version="10.0.0",
    description="Enterprise-grade AI Agent Platform"
)

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
# ROUTERS — fixed imports (removed 'app.' prefix)
# =========================================================

# STREAMING
try:
    from api.streaming_router import router as streaming_router
    app.include_router(streaming_router)
except Exception as e:
    print(f"[WARN] streaming_router skipped: {e}")

# STREAM ROUTES
try:
    from routes.stream_routes import router as stream_router
    app.include_router(stream_router, prefix="/api", tags=["Streaming & Agents"])
except Exception as e:
    print(f"[WARN] stream_router skipped: {e}")

# CHAT
try:
    from chat_routes import router as chat_router
    app.include_router(chat_router, prefix="/api/chat", tags=["Chat"])
except Exception as e:
    print(f"[WARN] chat_router skipped: {e}")

# AUTONOMOUS
try:
    from routes.autonomous_routes import router as autonomous_router
    app.include_router(autonomous_router, prefix="/api/autonomous", tags=["Autonomous AI"])
except Exception as e:
    print(f"[WARN] autonomous_router skipped: {e}")

# TOOLS
try:
    from routes.tools_routes import router as tools_router
    app.include_router(tools_router, prefix="/api/tools", tags=["Tools"])
except Exception as e:
    print(f"[WARN] tools_router skipped: {e}")

# UPLOAD
try:
    from routes.upload_routes import router as upload_router
    app.include_router(upload_router, prefix="/api/upload", tags=["Upload"])
except Exception as e:
    print(f"[WARN] upload_router skipped: {e}")

# FILES
try:
    from api.file_routes import router as file_router
    app.include_router(file_router, prefix="/api/files", tags=["Files"])
except Exception as e:
    print(f"[WARN] file_router skipped: {e}")

# PDF
try:
    from routes.pdf_routes import router as pdf_router
    app.include_router(pdf_router, prefix="/pdf", tags=["PDF"])
except Exception as e:
    print(f"[WARN] pdf_router skipped: {e}")

# RAG
try:
    from routes.rag_routes import router as rag_router
    app.include_router(rag_router, prefix="/api/rag", tags=["RAG"])
except Exception as e:
    print(f"[WARN] rag_router skipped: {e}")

# MEMORY
try:
    from routes.memory_routes import router as memory_router
    app.include_router(memory_router, prefix="/api/memory", tags=["Memory"])
except Exception as e:
    print(f"[WARN] memory_router skipped: {e}")

# VECTOR
try:
    from routes.vector_routes import router as vector_router
    app.include_router(vector_router, prefix="/api/vector", tags=["Vector"])
except Exception as e:
    print(f"[WARN] vector_router skipped: {e}")

# AUTH
try:
    from routes.auth_routes import router as auth_router
    app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
except Exception as e:
    print(f"[WARN] auth_router skipped: {e}")

# AGENTS
try:
    from routes.agent_routes import router as agent_router
    app.include_router(agent_router, prefix="/api/agents", tags=["Agents"])
except Exception as e:
    print(f"[WARN] agent_router skipped: {e}")

# TASKS
try:
    from routes.task_routes import router as task_router
    app.include_router(task_router, prefix="/api/tasks", tags=["Tasks"])
except Exception as e:
    print(f"[WARN] task_router skipped: {e}")

# TASK STATUS
try:
    from routes.task_status_routes import router as task_status_router
    app.include_router(task_status_router, prefix="/api/task-status", tags=["Task Status"])
except Exception as e:
    print(f"[WARN] task_status_router skipped: {e}")

# DISTRIBUTED
try:
    from routes.distributed_tasks import router as distributed_router
    app.include_router(distributed_router, prefix="/api/distributed", tags=["Distributed Tasks"])
except Exception as e:
    print(f"[WARN] distributed_router skipped: {e}")

# BROWSER
try:
    from routes.browser_routes import router as browser_router
    app.include_router(browser_router, prefix="/api/browser", tags=["Browser"])
except Exception as e:
    print(f"[WARN] browser_router skipped: {e}")

# ANALYTICS
try:
    from routes.analytics_routes import router as analytics_router
    app.include_router(analytics_router, prefix="/api/analytics", tags=["Analytics"])
except Exception as e:
    print(f"[WARN] analytics_router skipped: {e}")

# SETTINGS
try:
    from routes.settings_routes import router as settings_router
    app.include_router(settings_router, prefix="/api/settings", tags=["Settings"])
except Exception as e:
    print(f"[WARN] settings_router skipped: {e}")

# LEARNING
try:
    from routes.learning_routes import router as learning_router
    app.include_router(learning_router)
except Exception as e:
    print(f"[WARN] learning_router skipped: {e}")

# WEBSOCKET
try:
    from routes.websocket_routes import router as websocket_router
    app.include_router(websocket_router, prefix="/api", tags=["WebSocket"])
except Exception as e:
    print(f"[WARN] websocket_router skipped: {e}")

# =========================================================
# DATABASE + WORKER STARTUP (SYNC VERSION)
# =========================================================

@app.on_event("startup")
async def startup():
    # Database (sync version - no async)
    try:
        from database.database import engine, Base
        Base.metadata.create_all(bind=engine)
        print("[OK] Database initialized")
    except Exception as e:
        print(f"[WARN] Database skipped: {e}")

    # Worker manager
    try:
        from workers.worker_manager import worker_manager
        await worker_manager.start()
        print("[OK] Worker manager started")
    except Exception as e:
        print(f"[WARN] Worker manager skipped: {e}")

# =========================================================
# STATIC FILES + FRONTEND
# =========================================================

try:
    app.mount("/static", StaticFiles(directory="static"), name="static")

    FRONTEND_PATH = Path("static/index.html")

    @app.get("/app")
    async def frontend():
        return FileResponse(FRONTEND_PATH)
except Exception as e:
    print(f"[WARN] Static files skipped: {e}")

# =========================================================
# CORE ENDPOINTS
# =========================================================

@app.get("/")
async def root():
    return {"status": "ok", "project": "Nexora AI"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

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
