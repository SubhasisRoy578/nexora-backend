from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(
    title="Nexora AI",
    version="1.0.0",
    description="Enterprise-grade AI Agent Platform"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================
# HEALTH & INFO
# ==================

@app.get("/")
async def root():
    return {"status": "ok", "message": "Nexora AI Backend"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/analytics")
async def analytics():
    return {
        "avg_response": "1.4s",
        "success_rate": "97.8%",
        "tasks_today": 143,
        "tokens_used": "4.6M",
        "requests": [42, 78, 65, 91, 134, 87, 103],
        "tokens": [1.2, 2.1, 1.8, 2.6, 4.1, 2.4, 3.2]
    }

@app.get("/api/agents")
async def get_agents():
    return [
        {"id": "research", "name": "Research Agent", "status": "idle", "tasks": 47, "success": "98%"},
        {"id": "rag", "name": "RAG Agent", "status": "idle", "tasks": 134, "success": "99.1%"},
        {"id": "code", "name": "Code Agent", "status": "idle", "tasks": 29, "success": "96.2%"},
        {"id": "browser", "name": "Browser Agent", "status": "idle", "tasks": 12, "success": "94.5%"},
    ]

@app.post("/api/chat")
async def chat(message: str, tools: list = []):
    return {
        "response": f"You said: {message}",
        "tools_used": tools,
        "status": "success"
    }

@app.post("/api/upload")
async def upload():
    return {
        "id": "doc_123",
        "name": "document.pdf",
        "chunks": 100,
        "status": "indexed"
    }

@app.get("/api/knowledge")
async def knowledge():
    return [
        {"id": "doc_1", "name": "Market Report", "chunks": 923, "status": "indexed"},
        {"id": "doc_2", "name": "Competitor KB", "chunks": 128, "status": "indexed"},
    ]

@app.get("/capabilities")
async def capabilities():
    return {
        "chat": True,
        "streaming": True,
        "rag": True,
        "agents": True,
        "analytics": True,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
