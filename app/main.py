from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Nexora AI",
    version="1.0.0",
    description="AI Agent Platform"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── BASIC ENDPOINTS ───

@app.get("/")
async def root():
    return {"status": "ok", "project": "Nexora AI"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/chat")
async def chat():
    return {"message": "Chat endpoint working"}

@app.get("/api/agents")
async def agents():
    return {"agents": [], "status": "running"}

@app.get("/api/analytics")
async def analytics():
    return {"metrics": {}}

@app.get("/capabilities")
async def capabilities():
    return {
        "chat": True,
        "streaming": True,
        "agents": True,
        "rag": True,
        "analytics": True
    }
