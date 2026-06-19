import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from openai import OpenAI

from app.database import get_db
from app.simplified_rag import search_rag

router = APIRouter()
_client = None


def get_rag_client():
    global _client
    if _client is None:
        key = os.environ.get("OPENAI_API_KEY", "")
        if not key:
            print("[WARN] OPENAI_API_KEY is not set in environment.")
            key = "missing_key"
        _client = OpenAI(api_key=key)
    return _client


class RAGRequest(BaseModel):
    query: str
    user_id: str = "default_user"
    top_k: int = 3


@router.post("/retrieve")
async def retrieve_context(request: RAGRequest, db: Session = Depends(get_db)):
    """Return raw document chunks most relevant to the query."""
    try:
        results = search_rag(db, request.query, top_k=request.top_k)
        return {
            "query": request.query,
            "results": results,
            "total": len(results),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retrieval error: {e}")


@router.post("/ask")
async def ask_rag(request: RAGRequest, db: Session = Depends(get_db)):
    """Answer a question using retrieved document context."""
    try:
        results = search_rag(db, request.query, top_k=request.top_k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG search error: {e}")

    # If no relevant chunks found or low similarity, return clear message
    relevant_results = [r for r in results if r.get("similarity", 0) > 0.15]
    if not relevant_results:
        return {
            "success": False,
            "message": "No sufficiently relevant documents found. Please upload a document first.",
            "query": request.query,
            "answer": "No relevant documents found. Please upload a context document first.",
            "sources": []
        }

    context = "\n---\n".join([r["text"] for r in relevant_results])
    sources = list({r["filename"] for r in relevant_results})

    prompt = (
        f"Answer the question using only the context below.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {request.query}\n\n"
        f"If the answer is not in the context, say: 'I cannot find the answer in the provided documents.'"
    )

    try:
        client = get_rag_client()
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that answers questions based on provided document context."
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=1024,
        )
        answer = completion.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI error: {e}")

    return {
        "success": True,
        "query": request.query,
        "answer": answer,
        "sources": sources,
        "context_length": len(context),
    }


@router.get("/status")
async def rag_status(db: Session = Depends(get_db)):
    """Report the number of indexed chunks."""
    from app.models.document import DocumentChunk
    try:
        total_chunks = db.query(DocumentChunk).count()
        return {
            "rag_enabled": True,
            "total_chunks": total_chunks,
            "backend": "postgresql" if db.bind.dialect.name == 'postgresql' else "sqlite",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database status error: {e}")