import os
import math
from sqlalchemy.orm import Session
from app.ai.embeddings import create_embedding, create_embeddings


# ── Text Chunking ──────────────────────────────────────────────────────────────

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list:
    """Split text into overlapping chunks."""
    text = text.strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        # Ensure we make forward progress
        next_start = start + chunk_size - overlap
        if next_start <= start:
            break
        start = next_start
    return chunks


# ── File Text Extraction ───────────────────────────────────────────────────────

def extract_text_from_file(file_path: str) -> str:
    """Extract plain text from PDF, DOCX, or TXT."""
    ext = os.path.splitext(file_path)[1].lower()
    text = ""

    if ext == ".pdf":
        try:
            import fitz  # PyMuPDF is extremely lightweight
            doc = fitz.open(file_path)
            for page in doc:
                text += page.get_text()
            doc.close()
        except Exception as e:
            print(f"[PDF ERROR] PyMuPDF failed: {e}. Trying fallback pypdf...")
            try:
                import pypdf
                reader = pypdf.PdfReader(file_path)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text
            except Exception as e2:
                print(f"[PDF FALLBACK ERROR] {e2}")

    elif ext == ".docx":
        try:
            import docx
            doc = docx.Document(file_path)
            text = "\n".join(p.text for p in doc.paragraphs)
        except Exception as e:
            print(f"[DOCX ERROR] {e}")

    else:
        # Default fallback for TXT, MD, CSV etc.
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except Exception as e:
            print(f"[TXT ERROR] {e}")

    return text


# ── Document Indexing ──────────────────────────────────────────────────────────

def save_document(db: Session, file_path: str, filename: str) -> int:
    """Extract, chunk, embed, and persist a document to the database."""
    from app.models.document import DocumentChunk

    text = extract_text_from_file(file_path)
    if not text.strip():
        return 0

    chunks = chunk_text(text)
    if not chunks:
        return 0

    # Remove old chunks for this filename
    db.query(DocumentChunk).filter(DocumentChunk.filename == filename).delete()
    db.commit()

    # Batch embed all chunks in one request
    embeddings = create_embeddings(chunks)

    # Save chunks to database
    for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        record = DocumentChunk(
            filename=filename,
            chunk_index=i,
            text=chunk,
            embedding=emb
        )
        db.add(record)

    db.commit()
    return len(chunks)


# ── Similarity Search ──────────────────────────────────────────────────────────

def _cosine_similarity(v1: list, v2: list) -> float:
    dot = sum(a * b for a, b in zip(v1, v2))
    m1 = math.sqrt(sum(a * a for a in v1))
    m2 = math.sqrt(sum(b * b for b in v2))
    if m1 == 0 or m2 == 0:
        return 0.0
    return dot / (m1 * m2)


def search_rag(db: Session, query: str, top_k: int = 3) -> list:
    """Find top_k most similar chunks to the query from the database."""
    from app.models.document import DocumentChunk
    from app.database import HAS_PGVECTOR

    query_emb = create_embedding(query)
    
    # Use native pgvector operators if database is PostgreSQL and pgvector is enabled
    if db.bind.dialect.name == 'postgresql' and HAS_PGVECTOR:
        try:
            distance_expr = DocumentChunk.embedding.op('<=>')(query_emb)
            results = (
                db.query(DocumentChunk, (1.0 - distance_expr).label("similarity"))
                .order_by(distance_expr)
                .limit(top_k)
                .all()
            )
            return [
                {
                    "filename": r[0].filename,
                    "text": r[0].text,
                    "similarity": float(r[1] or 0.0)
                }
                for r in results
            ]
        except Exception as e:
            print(f"[PGVECTOR SEARCH ERROR] falling back to python similarity: {e}")

    # Fallback Python-based similarity search (e.g. on SQLite, or if pgvector is disabled)
    chunks = db.query(DocumentChunk).all()
    if not chunks:
        return []

    scored = []
    for chunk in chunks:
        if not chunk.embedding:
            continue
        sim = _cosine_similarity(query_emb, chunk.embedding)
        scored.append({
            "filename": chunk.filename,
            "text": chunk.text,
            "similarity": sim
        })

    scored.sort(key=lambda x: x["similarity"], reverse=True)
    return scored[:top_k]


# ── Chat Memory ────────────────────────────────────────────────────────────────

def store_message(db: Session, user_id: str, role: str, content: str):
    """Persist a chat turn to the database."""
    from app.models.chat import ChatMessage
    msg = ChatMessage(user_id=user_id, role=role, content=content)
    db.add(msg)
    db.commit()


def get_recent_messages(db: Session, user_id: str, limit: int = 10) -> list:
    """Retrieve the last N messages for a user."""
    from app.models.chat import ChatMessage
    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == user_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
        .all()
    )
    # Return in chronological order
    return [{"role": r.role, "content": r.content} for r in reversed(rows)]
