# app/llm_client.py
import os
import time
from typing import List, Dict, Any, Optional

# ============================================
# PROVIDER CLIENTS
# ============================================

def get_groq_client():
    try:
        from groq import Groq
        key = os.environ.get("GROQ_API_KEY")
        if key:
            return Groq(api_key=key)
    except ImportError:
        pass
    return None

def get_openai_client():
    try:
        from openai import OpenAI
        key = os.environ.get("OPENAI_API_KEY")
        if key:
            return OpenAI(api_key=key)
    except ImportError:
        pass
    return None

def get_gemini_client():
    try:
        import google.generativeai as genai
        key = os.environ.get("GEMINI_API_KEY")
        if key:
            genai.configure(api_key=key)
            return genai
    except ImportError:
        pass
    return None

# ============================================
# PROVIDER CALL FUNCTIONS
# ============================================

def call_groq(messages: List[Dict[str, str]]) -> tuple[str, str]:
    """Call Groq API."""
    client = get_groq_client()
    if not client:
        raise Exception("Groq client not available")
    
    model = os.environ.get("GROQ_MODEL", "llama3-70b-8192")
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=1024,
    )
    return response.choices[0].message.content, "groq"

def call_gemini(messages: List[Dict[str, str]]) -> tuple[str, str]:
    """Call Gemini API."""
    genai = get_gemini_client()
    if not genai:
        raise Exception("Gemini client not available")
    
    model = genai.GenerativeModel(os.environ.get("GEMINI_MODEL", "gemini-1.5-flash"))
    
    # Convert messages to Gemini format
    prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
    response = model.generate_content(prompt)
    return response.text, "gemini"

def call_openai(messages: List[Dict[str, str]]) -> tuple[str, str]:
    """Call OpenAI API."""
    client = get_openai_client()
    if not client:
        raise Exception("OpenAI client not available")
    
    model = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=1024,
    )
    return response.choices[0].message.content, "openai"

# ============================================
# FALLBACK CHAIN
# ============================================

PROVIDER_CHAIN = [
    ("groq", call_groq),
    ("gemini", call_gemini),
    ("openai", call_openai),
]

def get_chat_response(messages: List[Dict[str, str]]) -> tuple[str, str]:
    """
    Attempt to get a response from providers in order.
    Falls back to next provider if quota is exceeded.
    """
    errors = []
    
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
# TEST FUNCTION
# ============================================

def test_providers():
    """Test all providers and report status."""
    test_messages = [{"role": "user", "content": "Say 'hello' in one word."}]
    
    results = {}
    for name, func in PROVIDER_CHAIN:
        try:
            response, provider = func(test_messages)
            results[name] = {"status": "working", "response": response[:50]}
        except Exception as e:
            results[name] = {"status": "failed", "error": str(e)[:100]}
    
    return results
