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
# ROUTERS — USING RELATIVE IMPORTS (WITH DOTS)
# =========================================================

# STREAMING
try:
    from .api.streaming_router import router as streaming_router
    app.include_router(streaming_router)
    print("[LOADED] streaming_router")
except Exception as e:
    print(f"[FAILED] streaming_router: {e}")

# STREAM ROUTES
try:
    from .routes.stream_routes import router as stream_router
    app.include_router(stream_router, prefix="/api", tags=["Streaming & Agents"])
    print("[LOADED] stream_router")
except Exception as e:
    print(f"[FAILED] stream_router: {e}")

# CHAT
try:
    from .chat_routes import router as chat_router
    app.include_router(chat_router, prefix="/api/chat", tags=["Chat"])
    print("[LOADED] chat_router")
except Exception as e:
    print(f"[FAILED] chat_router: {e}")

# AUTONOMOUS
try:
    from .routes.autonomous_routes import router as autonomous_router
    app.include_router(autonomous_router, prefix="/api/autonomous", tags=["Autonomous AI"])
    print("[LOADED] autonomous_router")
except Exception as e:
    print(f"[FAILED] autonomous_router: {e}")

# TOOLS
try:
    from .routes.tools_routes import router as tools_router
    app.include_router(tools_router, prefix="/api/tools", tags=["Tools"])
    print("[LOADED] tools_router")
except Exception as e:
    print(f"[FAILED] tools_router: {e}")

# UPLOAD
try:
    from .routes.upload_routes import router as upload_router
    app.include_router(upload_router, prefix="/api/upload", tags=["Upload"])
    print("[LOADED] upload_router")
except Exception as e:
    print(f"[FAILED] upload_router: {e}")

# FILES
try:
    from .api.file_routes import router as file_router
    app.include_router(file_router, prefix="/api/files", tags=["Files"])
    print("[LOADED] file_router")
except Exception as e:
    print(f"[FAILED] file_router: {e}")

# PDF
try:
    from .routes.pdf_routes import router as pdf_router
    app.include_router(pdf_router, prefix="/pdf", tags=["PDF"])
    print("[LOADED] pdf_router")
except Exception as e:
    print(f"[FAILED] pdf_router: {e}")

# RAG
try:
    from .routes.rag_routes import router as rag_router
    app.include_router(rag_router, prefix="/api/rag", tags=["RAG"])
    print("[LOADED] rag_router")
except Exception as e:
    print(f"[FAILED] rag_router: {e}")

# MEMORY
try:
    from .routes.memory_routes import router as memory_router
    app.include_router(memory_router, prefix="/api/memory", tags=["Memory"])
    print("[LOADED] memory_router")
except Exception as e:
    print(f"[FAILED] memory_router: {e}")

# VECTOR
try:
    from .routes.vector_routes import router as vector_router
    app.include_router(vector_router, prefix="/api/vector", tags=["Vector"])
    print("[LOADED] vector_router")
except Exception as e:
    print(f"[FAILED] vector_router: {e}")

# AUTH
try:
    from .routes.auth_routes import router as auth_router
    app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
    print("[LOADED] auth_router")
except Exception as e:
    print(f"[FAILED] auth_router: {e}")

# AGENTS
try:
    from .routes.agent_routes import router as agent_router
    app.include_router(agent_router, prefix="/api/agents", tags=["Agents"])
    print("[LOADED] agent_router")
except Exception as e:
    print(f"[FAILED] agent_router: {e}")

# TASKS
try:
    from .routes.task_routes import router as task_router
    app.include_router(task_router, prefix="/api/tasks", tags=["Tasks"])
    print("[LOADED] task_router")
except Exception as e:
    print(f"[FAILED] task_router: {e}")

# TASK STATUS
try:
    from .routes.task_status_routes import router as task_status_router
    app.include_router(task_status_router, prefix="/api/task-status", tags=["Task Status"])
    print("[LOADED] task_status_router")
except Exception as e:
    print(f"[FAILED] task_status_router: {e}")

# DISTRIBUTED
try:
    from .routes.distributed_tasks import router as distributed_router
    app.include_router(distributed_router, prefix="/api/distributed", tags=["Distributed Tasks"])
    print("[LOADED] distributed_router")
except Exception as e:
    print(f"[FAILED] distributed_router: {e}")

# BROWSER
try:
    from .routes.browser_routes import router as browser_router
    app.include_router(browser_router, prefix="/api/browser", tags=["Browser"])
    print("[LOADED] browser_router")
except Exception as e:
    print(f"[FAILED] browser_router: {e}")

# ANALYTICS
try:
    from .routes.analytics_routes import router as analytics_router
    app.include_router(analytics_router, prefix="/api/analytics", tags=["Analytics"])
    print("[LOADED] analytics_router")
except Exception as e:
    print(f"[FAILED] analytics_router: {e}")

# SETTINGS
try:
    from .routes.settings_routes import router as settings_router
    app.include_router(settings_router, prefix="/api/settings", tags=["Settings"])
    print("[LOADED] settings_router")
except Exception as e:
    print(f"[FAILED] settings_router: {e}")

# LEARNING
try:
    from .routes.learning_routes import router as learning_router
    app.include_router(learning_router)
    print("[LOADED] learning_router")
except Exception as e:
    print(f"[FAILED] learning_router: {e}")

# WEBSOCKET
try:
    from .routes.websocket_routes import router as websocket_router
    app.include_router(websocket_router, prefix="/api", tags=["WebSocket"])
    print("[LOADED] websocket_router")
except Exception as e:
    print(f"[FAILED] websocket_router: {e}")

# =========================================================
# DATABASE + WORKER STARTUP
# =========================================================

@app.on_event("startup")
async def startup():
    # Database
    try:
        from .database import engine, Base
        Base.metadata.create_all(bind=engine)
        print("[OK] Database initialized")
    except Exception as e:
        print(f"[WARN] Database skipped: {e}")

    # Worker manager
    try:
        from .workers.worker_manager import worker_manager
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
    print("[OK] Static files mounted")
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
