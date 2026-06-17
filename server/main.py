from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from server.db import init_db, close_db, get_redis
from server.routers.chat import router as chat_router

app = FastAPI()

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(chat_router)

@app.get("/")
async def root():
    return {"message": "Nexora AI Backend Running"}