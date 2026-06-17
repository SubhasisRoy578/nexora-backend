import os
import json
import math
from openai import OpenAI
import fitz  # PyMuPDF
import docx

# Initialize OpenAI client using environment variable
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "dummy_key"))

RAG_STORE_FILE = "simplified_rag_store.json"
MEMORIES_FILE = "simplified_memories.json"

def get_embedding(text: str) -> list:
    """Generate embedding for a given text using OpenAI API."""
    try:
        response = client.embeddings.create(
            input=[text.replace("\n", " ")],
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error generating embedding: {e}")
        # Return a zero vector of dimension 1536 as fallback
        return [0.0] * 1536

def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> list:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    text_len = len(text)
    
    if text_len <= chunk_size:
        return [text]
        
    while start < text_len:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += (chunk_size - chunk_overlap)
        
    return chunks

def extract_text_from_file(file_path: str) -> str:
    """Extract plain text from PDF, DOCX, or TXT file."""
    ext = os.path.splitext(file_path)[1].lower()
    text = ""
    
    if ext == ".pdf":
        try:
            doc = fitz.open(file_path)
            for page in doc:
                text += page.get_text()
            doc.close()
        except Exception as e:
            print(f"Error reading PDF {file_path}: {e}")
    elif ext == ".docx":
        try:
            doc = docx.Document(file_path)
            text = "\n".join([p.text for p in doc.paragraphs])
        except Exception as e:
            print(f"Error reading DOCX {file_path}: {e}")
    else:
        # Default to text file
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except Exception as e:
            print(f"Error reading text file {file_path}: {e}")
            
    return text

def save_document(file_path: str, filename: str) -> int:
    """Process a document, chunk it, embed chunks, and save to JSON store."""
    text = extract_text_from_file(file_path)
    if not text.strip():
        return 0
        
    chunks = chunk_text(text)
    
    # Load existing store
    store = []
    if os.path.exists(RAG_STORE_FILE):
        try:
            with open(RAG_STORE_FILE, "r", encoding="utf-8") as f:
                store = json.load(f)
        except Exception as e:
            print(f"Error loading RAG store: {e}")
            store = []
            
    # Remove old chunks for the same file if any
    store = [entry for entry in store if entry.get("filename") != filename]
    
    # Process and embed each chunk
    for chunk in chunks:
        embedding = get_embedding(chunk)
        store.append({
            "filename": filename,
            "text": chunk,
            "embedding": embedding
        })
        
    # Write back to store
    try:
        with open(RAG_STORE_FILE, "w", encoding="utf-8") as f:
            json.dump(store, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error writing to RAG store: {e}")
        
    return len(chunks)

def dot_product(v1: list, v2: list) -> float:
    return sum(x * y for x, y in zip(v1, v2))

def magnitude(v: list) -> float:
    return math.sqrt(sum(x * x for x in v))

def cosine_similarity(v1: list, v2: list) -> float:
    m1 = magnitude(v1)
    m2 = magnitude(v2)
    if m1 == 0.0 or m2 == 0.0:
        return 0.0
    return dot_product(v1, v2) / (m1 * m2)

def search_rag(query: str, top_k: int = 3) -> list:
    """Find the most similar chunks from the RAG store for the query."""
    if not os.path.exists(RAG_STORE_FILE):
        return []
        
    try:
        with open(RAG_STORE_FILE, "r", encoding="utf-8") as f:
            store = json.load(f)
    except Exception as e:
        print(f"Error loading RAG store for search: {e}")
        return []
        
    if not store:
        return []
        
    query_emb = get_embedding(query)
    
    scored_chunks = []
    for entry in store:
        emb = entry.get("embedding")
        if not emb:
            continue
        sim = cosine_similarity(query_emb, emb)
        scored_chunks.append({
            "filename": entry.get("filename"),
            "text": entry.get("text"),
            "similarity": sim
        })
        
    # Sort descending by similarity
    scored_chunks.sort(key=lambda x: x["similarity"], reverse=True)
    return scored_chunks[:top_k]

# Simple Memory Helper
def store_memory(user_id: str, role: str, content: str):
    memories = {}
    if os.path.exists(MEMORIES_FILE):
        try:
            with open(MEMORIES_FILE, "r", encoding="utf-8") as f:
                memories = json.load(f)
        except Exception:
            memories = {}
            
    if user_id not in memories:
        memories[user_id] = []
        
    memories[user_id].append(f"{role}: {content}")
    # Keep last 10 turns of history
    memories[user_id] = memories[user_id][-20:]
    
    try:
        with open(MEMORIES_FILE, "w", encoding="utf-8") as f:
            json.dump(memories, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving memories: {e}")

def get_memories(user_id: str) -> list:
    if not os.path.exists(MEMORIES_FILE):
        return []
    try:
        with open(MEMORIES_FILE, "r", encoding="utf-8") as f:
            memories = json.load(f)
        return memories.get(user_id, [])
    except Exception:
        return []
