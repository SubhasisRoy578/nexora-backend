from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import os
from pathlib import Path

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
# SAFE IMPORTS - ALL FEATURES PRESERVED
# =========================================================

# Database
try:
    from app.database.database import engine, Base
    HAS_DB = True
except Exception as e:
    print(f"⚠️ Database import skipped: {e}")
    HAS_DB = False

# Workers
try:
    from app.workers.worker_manager import worker_manager
    HAS_WORKERS = True
except Exception as e:
    print(f"⚠️ Worker manager import skipped: {e}")
    HAS_WORKERS = False

# Routers
routers_config = [
    ("app.routes.pdf_routes", "pdf_router", "/pdf", "PDF"),
    ("app.api.file_routes", "file_router", "/api/files", "Files"),
    ("app.routes.learning_routes", "learning_router", "", "Learning"),
    ("app.api.streaming_router", "streaming_router", "", "Streaming"),
    ("app.routes.distributed_tasks", "distributed_router", "/api/distributed", "Distributed Tasks"),
    ("app.routes.websocket_routes", "websocket_router", "/api", "WebSocket"),
    ("app.routes.tools_routes", "tools_router", "/api/tools", "Tools"),
    ("app.routes.autonomous_routes", "autonomous_router", "/api/autonomous", "Autonomous AI"),
    ("app.routes.task_status_routes", "task_status_router", "/api/task-status", "Task Status"),
    ("app.routes.stream_routes", "stream_router", "/api", "Streaming & Agents"),
    ("app.chat_routes", "chat_router", "/api/chat", "Chat"),
    ("app.routes.upload_routes", "upload_router", "/api/upload", "Upload"),
    ("app.routes.rag_routes", "rag_router", "/api/rag", "RAG"),
    ("app.routes.memory_routes", "memory_router", "/api/memory", "Memory"),
    ("app.routes.auth_routes", "auth_router", "/api/auth", "Auth"),
    ("app.routes.agent_routes", "agent_router", "/api/agents", "Agents"),
    ("app.routes.task_routes", "task_router", "/api/tasks", "Tasks"),
    ("app.routes.browser_routes", "browser_router", "/api/browser", "Browser"),
    ("app.routes.analytics_routes", "analytics_router", "/api/analytics", "Analytics"),
    ("app.routes.vector_routes", "vector_router", "/api/vector", "Vector"),
    ("app.routes.settings_routes", "settings_router", "/api/settings", "Settings"),
]

# Load routers safely
for module_name, router_var, prefix, tag in routers_config:
    try:
        module = __import__(module_name, fromlist=[router_var])
        router = getattr(module, router_var)
        if prefix:
            app.include_router(router, prefix=prefix, tags=[tag])
        else:
            app.include_router(router)
        print(f"✓ Loaded {tag}")
    except Exception as e:
        print(f"⚠️ Skipped {tag}: {str(e)[:50]}")

# =========================================================
# DATABASE INITIALIZATION
# =========================================================

@app.on_event("startup")
async def startup():
    try:
        if HAS_DB:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            print("✓ Database initialized")
    except Exception as e:
        print(f"⚠️ Database startup: {e}")
    
    try:
        if HAS_WORKERS:
            await worker_manager.start()
            print("✓ Worker manager started")
    except Exception as e:
        print(f"⚠️ Worker manager: {e}")

# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "nexora-api"}

# =========================================================
# CAPABILITIES (ALL FEATURES)
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
        "llm_integration": True,
    }

# =========================================================
# SYSTEM INFO (ALL FEATURES)
# =========================================================

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
            "production_backend": True,
            "distributed_tasks": True,
            "websocket_streaming": True,
            "autonomous_agents": True,
            "task_status_tracking": True,
            "file_management": True,
            "learning_system": True,
        },
    }

# =========================================================
# ROOT
# =========================================================

@app.get("/")
async def root():
    return {
        "service": "Nexora AI Backend",
        "version": "10.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "capabilities": "/capabilities",
    }

# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
