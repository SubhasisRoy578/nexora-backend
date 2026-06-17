from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    model: str = "gemini"

class MemoryRequest(BaseModel):
    text: str