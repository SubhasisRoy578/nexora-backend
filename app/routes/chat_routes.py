import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from app.database import get_db
from app.simplified_rag import search_rag, store_message, get_recent_messages

router = APIRouter()

# ============================================
# GROQ CLIENT (Default - Free, Fast, Works on Render)
# ============================================

def get_groq_client():
    """Initialize Groq client with API key."""
    from groq import Groq
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        raise ValueError("GROQ_API_KEY environment variable is not set")
    return Groq(api_key=key)

def call_groq(messages: list) -> str:
    """Call Groq API for chat completion."""
    try:
        client = get_groq_client()
        model = os.environ.get("GROQ_MODEL", "llama3-70b-8192")
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=1024,
        )
        return response.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Groq API error: {e}")

# ============================================
# OLLAMA (Optional - Only for local testing)
# ============================================

def call_ollama(messages: list) -> str:
    """Call Ollama API (only works locally)."""
    try:
        import ollama
        model = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")
        response = ollama.chat(model=model, messages=messages)
        return response["message"]["content"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ollama API error: {e}")

# ============================================
# LLM ROUTER
# ============================================

def get_chat_response(messages: list, provider: Optional[str] = None) -> tuple[str, str]:
    """Route to the appropriate LLM provider."""
    # Default to Groq for Render deployment
    active_provider = provider or os.environ.get("LLM_PROVIDER", "groq").lower()
    
    if active_provider == "groq":
        return call_groq(messages), "groq"
    elif active_provider == "ollama":
        return call_ollama(messages), "ollama"
    else:
        # Fallback to Groq
        return call_groq(messages), "groq (fallback)"

# ============================================
# REQUEST MODEL
# ============================================

class ChatRequest(BaseModel):
    user_id: str
    message: str
    provider: Optional[str] = None

# ============================================
# CHAT ENDPOINT
# ============================================

@router.post("/chat")
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    user_id = request.user_id
    message = request.message

    # 1. Retrieve recent messages from DB for conversation history
    history = []
    try:
        history = get_recent_messages(db, user_id=user_id, limit=10)
    except Exception as e:
        print(f"[DB history error]: {e}")

    # 2. Search for relevant context using RAG
    rag_context = ""
    sources = []
    try:
        rag_results = search_rag(db, message, top_k=3)
        if rag_results:
            filtered_results = [r for r in rag_results if r.get("similarity", 0) > 0.15]
            if filtered_results:
                rag_context = "\n---\n".join([r["text"] for r in filtered_results])
                sources = list({r["filename"] for r in filtered_results})
    except Exception as e:
        print(f"[RAG Retrieval Error]: {e}")

    # 3. Construct prompts
    system_prompt = "You are Nexora AI, a helpful, intelligent AI assistant."
    if rag_context:
        system_prompt += (
            f"\n\nContext from user's uploaded documents:\n{rag_context}\n\n"
            f"Instructions: Answer the question using the context above when relevant. "
            f"If the context doesn't contain the answer, use your general knowledge to answer, "
            f"but clearly state that the answer was not found in the uploaded documents."
        )

    messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": message})

    # 4. Call the selected LLM provider
    try:
        ai_response, provider_used = get_chat_response(messages, request.provider)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM API error: {e}")

    # 5. Persist messages to database
    try:
        store_message(db, user_id, "user", message)
        store_message(db, user_id, "assistant", ai_response)
    except Exception as e:
        print(f"[DB memory write error]: {e}")

    return {
        "success": True,
        "response": ai_response,
        "provider_used": provider_used,
        "sources": sources,
        "history_count": len(history)
    }

# ============================================
# HISTORY ENDPOINTS
# ============================================

@router.get("/history/{user_id}")
async def get_history(user_id: str, db: Session = Depends(get_db)):
    try:
        history = get_recent_messages(db, user_id=user_id, limit=50)
        return {"success": True, "history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@router.delete("/history/{user_id}")
async def clear_history(user_id: str, db: Session = Depends(get_db)):
    from app.models.chat import ChatMessage
    try:
        deleted = db.query(ChatMessage).filter(ChatMessage.user_id == user_id).delete()
        db.commit()
        return {"success": True, "deleted_count": deleted}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

# ============================================
# TEST ENDPOINT
# ============================================

@router.get("/test")
async def test_chat():
    return {
        "status": "ok",
        "message": "Chat router is working!",
        "llm_provider": os.environ.get("LLM_PROVIDER", "groq")
    }
