from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv()

app = FastAPI(
    title="Nexora AI",
    version="10.0.0",
    description="Enterprise-grade AI Agent Platform"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load simplified routers only to prevent Out Of Memory (OOM) on 512MB RAM instances
try:
    from .chat_routes import router as chat_router
    app.include_router(chat_router, prefix="/api/chat", tags=["Chat"])
    print("[LOADED] chat_router")
except Exception as e:
    print(f"[FAILED] chat_router: {e}")

try:
    from .routes.upload_routes import router as upload_router
    app.include_router(upload_router, prefix="/api/upload", tags=["Upload"])
    print("[LOADED] upload_router")
except Exception as e:
    print(f"[FAILED] upload_router: {e}")

try:
    from .routes.rag_routes import router as rag_router
    app.include_router(rag_router, prefix="/api/rag", tags=["RAG"])
    print("[LOADED] rag_router")
except Exception as e:
    print(f"[FAILED] rag_router: {e}")

# Static Files
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
    FRONTEND_PATH = Path("static/index.html")
    @app.get("/app")
    async def frontend():
        return FileResponse(FRONTEND_PATH)
    print("[OK] Static files mounted")
except Exception as e:
    print(f"[WARN] Static files skipped: {e}")

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
        "memory": True,
        "rag": True,
        "pdf_upload": True,
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
            "rag": True,
            "document_intelligence": True,
            "large_file_uploads": True,
            "production_backend": True
        }
    }