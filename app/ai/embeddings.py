import os
from openai import OpenAI

_client = None
EMBED_MODEL = "text-embedding-ada-002"
EMBED_DIM = 1536

def get_client():
    global _client
    if _client is None:
        key = os.environ.get("OPENAI_API_KEY", "")
        if not key:
            print("[WARN] OPENAI_API_KEY is not set in environment.")
            key = "missing_key"
        _client = OpenAI(api_key=key)
    return _client


# ==================================================
# SINGLE EMBEDDING
# ==================================================

def create_embedding(text: str) -> list:
    """
    Encodes a single string into a vector using OpenAI embeddings.
    Returns a list of floats.
    """
    cleaned_text = text.replace("\n", " ").strip()
    if not cleaned_text:
        return [0.0] * EMBED_DIM
    try:
        client = get_client()
        resp = client.embeddings.create(
            input=[cleaned_text[:8000]],
            model=EMBED_MODEL
        )
        return resp.data[0].embedding
    except Exception as e:
        print(f"[EMBED ERROR] OpenAI failed: {e}")
        return [0.0] * EMBED_DIM


# ==================================================
# BATCH EMBEDDINGS
# ==================================================

def create_embeddings(texts: list) -> list:
    """
    Encodes a list of strings into a list of vectors.
    Each vector is a list of floats.
    """
    if not texts:
        return []
    try:
        cleaned_texts = [t.replace("\n", " ").strip()[:8000] for t in texts]
        non_empty = [(i, t) for i, t in enumerate(cleaned_texts) if t]
        
        results = [[0.0] * EMBED_DIM for _ in range(len(texts))]
        if not non_empty:
            return results
            
        client = get_client()
        resp = client.embeddings.create(
            input=[item[1] for item in non_empty],
            model=EMBED_MODEL
        )
        
        for idx, data_item in enumerate(resp.data):
            original_idx = non_empty[idx][0]
            results[original_idx] = data_item.embedding
            
        return results
    except Exception as e:
        print(f"[EMBED BATCH ERROR] OpenAI failed: {e}")
        return [create_embedding(t) for t in texts]
