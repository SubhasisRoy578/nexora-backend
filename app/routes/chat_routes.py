# app/routes/chat_routes.py
import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from app.database import get_db
from app.simplified_rag import search_rag, store_message, get_recent_messages

router = APIRouter()

# ============================================
# PROVIDER CLIENTS
# ============================================

def get_groq_client():
    """Initialize Groq client with API key."""
    try:
        from groq import Groq
        key = os.environ.get("GROQ_API_KEY")
        if not key:
            print("[WARN] GROQ_API_KEY not set")
            return None
        return Groq(api_key=key)
    except ImportError:
        print("[WARN] Groq library not installed")
        return None

def get_openai_client():
    """Initialize OpenAI client with API key."""
    try:
        from openai import OpenAI
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            print("[WARN] OPENAI_API_KEY not set")
            return None
        return OpenAI(api_key=key)
    except ImportError:
        print("[WARN] OpenAI library not installed")
        return None

def get_gemini_client():
    """Initialize Gemini client with API key."""
    try:
        import google.generativeai as genai
        key = os.environ.get("GEMINI_API_KEY")
        if not key:
            print("[WARN] GEMINI_API_KEY not set")
            return None
        genai.configure(api_key=key)
        return genai
    except ImportError:
        print("[WARN] Google Generative AI library not installed")
        return None

# ============================================
# PROVIDER CALL FUNCTIONS
# ============================================

def call_groq(messages: list) -> tuple[str, str]:
    """Call Groq API for chat completion."""
    client = get_groq_client()
    if not client:
        raise Exception("Groq client not available. Check GROQ_API_KEY.")
    
    model = os.environ.get("GROQ_MODEL", "llama3-70b-8192")
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=1024,
    )
    return response.choices[0].message.content, "groq"

def call_openai(messages: list) -> tuple[str, str]:
    """Call OpenAI API for chat completion."""
    client = get_openai_client()
    if not client:
        raise Exception("OpenAI client not available. Check OPENAI_API_KEY.")
    
    model = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=1024,
    )
    return response.choices[0].message.content, "openai"

def call_gemini(messages: list) -> tuple[str, str]:
    """Call Gemini API for chat completion."""
    genai = get_gemini_client()
    if not genai:
        raise Exception("Gemini client not available. Check GEMINI_API_KEY.")
    
    model = genai.GenerativeModel(os.environ.get("GEMINI_MODEL", "gemini-1.5-flash"))
    
    # Convert messages to Gemini format
    prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
    response = model.generate_content(prompt)
    return response.text, "gemini"

def call_ollama(messages: list) -> tuple[str, str]:
    """Call Ollama API (only works locally)."""
    try:
        import ollama
        model = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")
        response = ollama.chat(model=model, messages=messages)
        return response["message"]["content"], "ollama"
    except Exception as e:
        raise Exception(f"Ollama error: {e}")

# ============================================
# FALLBACK CHAIN
# ============================================

PROVIDER_CHAIN = [
    ("groq", call_groq),
    ("gemini", call_gemini),
    ("openai", call_openai),
]

def get_chat_response(messages: list, provider: Optional[str] = None) -> tuple[str, str]:
    """
    Route to the appropriate LLM provider with automatic fallback.
    If a specific provider is requested, try it first, then fallback.
    """
    errors = []
    
    # If a specific provider is requested, try it first
    if provider:
        provider_map = {
            "groq": call_groq,
            "gemini": call_gemini,
            "openai": call_openai,
            "ollama": call_ollama,
        }
        if provider in provider_map:
            try:
                print(f"[LLM] Attempting requested provider: {provider}")
                response, used_provider = provider_map[provider](messages)
                print(f"[LLM] Success with {used_provider}")
                return response, used_provider
            except Exception as e:
                error_msg = str(e)
                print(f"[LLM] Requested provider {provider} failed: {error_msg}")
                errors.append(f"{provider}: {error_msg}")
                # Fall through to fallback chain
    
    # Try providers in order
    for provider_name, provider_func in PROVIDER_CHAIN:
        try:
            print(f"[LLM] Attempting {provider_name}...")
            response, used_provider = provider_func(messages)
            print(f"[LLM] Success with {used_provider}")
            return response, used_provider
            
        except Exception as e:
            error_msg = str(e)
            print(f"[LLM] {provider_name} failed: {error_msg}")
            errors.append(f"{provider_name}: {error_msg}")
            
            # Check if it's a quota/rate limit error
            if any(keyword in error_msg.lower() for keyword in ['quota', 'rate', 'limit', 'exceeded']):
                print(f"[LLM] {provider_name} quota exceeded, falling back...")
                continue
            else:
                # For other errors, try the next provider anyway
                continue
    
    # All providers failed
    raise Exception(f"All providers failed: {'; '.join(errors)}")

# ============================================
# REQUEST MODEL
# ============================================

class ChatRequest(BaseModel):
    user_id: str
    message: str
    provider: Optional[str] = None  # Allows forcing a specific provider

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

    # 4. Call the selected LLM provider with fallback
    try:
        ai_response, provider_used = get_chat_response(messages, request.provider)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM API error: {str(e)}")

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
# TEST ENDPOINTS
# ============================================

@router.get("/test")
async def test_chat():
    """Test if the chat router is working."""
    return {
        "status": "ok",
        "message": "Chat router is working with fallback architecture!",
        "providers_configured": {
            "groq": bool(os.environ.get("GROQ_API_KEY")),
            "gemini": bool(os.environ.get("GEMINI_API_KEY")),
            "openai": bool(os.environ.get("OPENAI_API_KEY")),
            "ollama": bool(os.environ.get("OLLAMA_MODEL")),
        },
        "active_provider": os.environ.get("LLM_PROVIDER", "groq")
    }

@router.get("/test/providers")
async def test_all_providers():
    """Test all LLM providers and report status."""
    test_messages = [{"role": "user", "content": "Say 'hello' in one word."}]
    
    results = {}
    providers = {
        "groq": call_groq,
        "gemini": call_gemini,
        "openai": call_openai,
    }
    
    for name, func in providers.items():
        try:
            response, provider = func(test_messages)
            results[name] = {"status": "working", "response": response[:50]}
        except Exception as e:
            results[name] = {"status": "failed", "error": str(e)[:100]}
    
    return {"success": True, "results": results}
