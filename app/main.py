"""
Nexora AI — FastAPI entry point.
Optimized for Render free tier (512 MB RAM).
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv()

# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Nexora AI",
    version="11.0.0",
    description="Nexora AI — RAG-powered chat with persistent PostgreSQL storage",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Database Init ──────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    try:
        from app.database import init_db
        init_db()
    except Exception as e:
        print(f"[WARN] DB init failed: {e}")


# ── Routers ────────────────────────────────────────────────────────────────────
from app.routes.chat_routes import router as chat_router
from app.routes.upload_routes import router as upload_router
from app.routes.rag_routes import router as rag_router
from app.routes.vector_routes import router as vector_router
from app.routes.auth_routes import router as auth_router
from app.routes.analytics_routes import router as analytics_router
from app.routes.settings_routes import router as settings_router
from app.routes.learning_routes import router as learning_router
from app.routes.websocket_routes import router as websocket_router
from app.routes.browser_routes import router as browser_router

app.include_router(chat_router, prefix="/api/chat", tags=["Chat"])
app.include_router(upload_router, prefix="/api/upload", tags=["Upload"])
app.include_router(rag_router, prefix="/api/rag", tags=["RAG"])
app.include_router(vector_router, prefix="/api/vector", tags=["Vector"])
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(analytics_router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(settings_router, prefix="/api/settings", tags=["Settings"])
app.include_router(learning_router, prefix="/api/learning", tags=["Learning"])
app.include_router(websocket_router, prefix="/api/websocket", tags=["Websocket"])
app.include_router(browser_router, prefix="/api/browser", tags=["Browser"])

print("[OK] All 10 simplified routers registered successfully")


# ── Static / Frontend ──────────────────────────────────────────────────────────
try:
    static_dir = Path("static")
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory="static"), name="static")
        FRONTEND_PATH = static_dir / "index.html"

        @app.get("/app")
        async def frontend():
            return FileResponse(FRONTEND_PATH)

        print("[OK] Static files mounted")
except Exception as e:
    print(f"[WARN] Static files skipped: {e}")


# ── Health & Info ──────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {"status": "ok", "project": "Nexora AI", "version": "11.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/capabilities")
async def capabilities():
    return {
        "chat": True,
        "rag": True,
        "file_upload": True,
        "persistent_memory": True,
        "openai_embeddings": True,
        "postgresql_backend": True,
    }