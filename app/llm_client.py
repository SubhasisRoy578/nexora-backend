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
    """Call Groq API with updated working models."""
    client = get_groq_client()
    if not client:
        raise Exception("Groq client not available. Check GROQ_API_KEY.")
    
    # Updated to working models - use environment variable or fallback
    model = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")
    
    # List of known working Groq models (for reference)
    WORKING_MODELS = [
        "llama-3.1-8b-instant",
        "llama-3.1-70b-versatile",
        "mixtral-8x7b-32768",
        "gemma2-9b-it",
        "llama3-70b-8192",  # Still works for some users
    ]
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=1024,
            temperature=0.7,
        )
        return response.choices[0].message.content, "groq"
    except Exception as e:
        error_str = str(e)
        # Provide helpful error message for decommissioned models
        if "decommissioned" in error_str.lower():
            raise Exception(
                f"Groq model '{model}' is decommissioned. "
                f"Please update GROQ_MODEL to one of: {', '.join(WORKING_MODELS)}"
            )
        raise Exception(f"Groq API error: {e}")

def call_gemini(messages: List[Dict[str, str]]) -> tuple[str, str]:
    """Call Gemini API."""
    genai = get_gemini_client()
    if not genai:
        raise Exception("Gemini client not available. Check GEMINI_API_KEY.")
    
    model_name = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
    
    try:
        model = genai.GenerativeModel(model_name)
        
        # Convert messages to Gemini format
        prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        response = model.generate_content(prompt)
        
        if response.text:
            return response.text, "gemini"
        else:
            raise Exception("Gemini returned empty response")
            
    except Exception as e:
        error_str = str(e)
        if "API key" in error_str.lower() or "invalid" in error_str.lower():
            raise Exception(f"Gemini API key invalid. Check GEMINI_API_KEY.")
        raise Exception(f"Gemini API error: {e}")

def call_openai(messages: List[Dict[str, str]]) -> tuple[str, str]:
    """Call OpenAI API."""
    client = get_openai_client()
    if not client:
        raise Exception("OpenAI client not available. Check OPENAI_API_KEY.")
    
    model = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=1024,
            temperature=0.7,
        )
        return response.choices[0].message.content, "openai"
    except Exception as e:
        error_str = str(e)
        if "quota" in error_str.lower() or "exceeded" in error_str.lower():
            raise Exception(f"OpenAI quota exceeded. Check your billing.")
        raise Exception(f"OpenAI API error: {e}")

def call_ollama(messages: List[Dict[str, str]]) -> tuple[str, str]:
    """Call Ollama API (only works locally)."""
    try:
        import ollama
        model = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")
        response = ollama.chat(model=model, messages=messages)
        return response["message"]["content"], "ollama"
    except ImportError:
        raise Exception("Ollama library not installed. Run: pip install ollama")
    except Exception as e:
        raise Exception(f"Ollama API error: {e}")

# ============================================
# FALLBACK CHAIN
# ============================================

PROVIDER_CHAIN = [
    ("groq", call_groq),
    ("gemini", call_gemini),
    ("openai", call_openai),
]

def get_chat_response(messages: List[Dict[str, str]], provider: Optional[str] = None) -> tuple[str, str]:
    """
    Attempt to get a response from providers in order.
    Falls back to next provider if quota is exceeded.
    
    Args:
        messages: List of message dictionaries with 'role' and 'content'
        provider: Optional specific provider to try first
    
    Returns:
        Tuple of (response_text, provider_used)
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

# ============================================
# HEALTH CHECK
# ============================================

def get_provider_status() -> Dict[str, bool]:
    """Check which providers are configured."""
    return {
        "groq": bool(os.environ.get("GROQ_API_KEY")),
        "gemini": bool(os.environ.get("GEMINI_API_KEY")),
        "openai": bool(os.environ.get("OPENAI_API_KEY")),
        "ollama": bool(os.environ.get("OLLAMA_MODEL")),
    }

def get_working_models() -> Dict[str, List[str]]:
    """Return list of working models for each provider."""
    return {
        "groq": [
            "llama-3.1-8b-instant",
            "llama-3.1-70b-versatile",
            "mixtral-8x7b-32768",
            "gemma2-9b-it",
        ],
        "gemini": [
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-2.0-flash-exp",
        ],
        "openai": [
            "gpt-3.5-turbo",
            "gpt-4",
            "gpt-4-turbo-preview",
        ]
    }
