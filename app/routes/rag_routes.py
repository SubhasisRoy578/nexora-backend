from fastapi import APIRouter
from pydantic import BaseModel

from ..rag.rag_engine import RAGEngine
from ..llm.llm_router import ask_llm

router = APIRouter()
rag_engine = RAGEngine()


# ==================================================
# MODELS
# ==================================================

class RAGRequest(BaseModel):
    user_id: str
    query: str


# ==================================================
# RETRIEVE CONTEXT
# ==================================================

@router.post("/retrieve")
async def retrieve_context(request: RAGRequest):
    context = rag_engine.generate_context(
        user_id=request.user_id,
        query=request.query
    )
    return {"query": request.query, "context": context}


# ==================================================
# ASK RAG
# ==================================================

@router.post("/ask")
async def ask_rag(request: RAGRequest):
    context = rag_engine.generate_context(
        user_id=request.user_id,
        query=request.query
    )

    if not context:
        return {
            "success": False,
            "message": "No relevant documents found"
        }

    prompt = f"""
    Answer the question using the context.

    Context:
    {context}

    Question:
    {request.query}

    Give a detailed answer.
    """

    answer = await ask_llm(prompt)

    return {
        "success": True,
        "query": request.query,
        "answer": answer,
        "context_length": len(context)
    }


# ==================================================
# RAG STATUS
# ==================================================

@router.get("/status")
async def rag_status():
    return {
        "rag_enabled": True,
        "llm_enabled": True,
        "document_retrieval": True,
        "semantic_search": True
    }
