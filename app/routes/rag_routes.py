from fastapi import APIRouter
from pydantic import BaseModel
from openai import OpenAI
import os
from app.simplified_rag import search_rag

router = APIRouter()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "dummy_key"))


class RAGRequest(BaseModel):
    user_id: str
    query: str


@router.post("/retrieve")
async def retrieve_context(request: RAGRequest):
    rag_results = search_rag(request.query, top_k=3)
    context = "\n---\n".join([chunk["text"] for chunk in rag_results])
    return {
        "query": request.query,
        "context": context
    }


@router.post("/ask")
async def ask_rag(request: RAGRequest):
    rag_results = search_rag(request.query, top_k=3)
    context = "\n---\n".join([chunk["text"] for chunk in rag_results])

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

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant answering queries based on document context."},
                {"role": "user", "content": prompt}
            ]
        )
        answer = completion.choices[0].message.content
    except Exception as e:
        answer = f"Error calling OpenAI API: {e}"

    return {
        "success": True,
        "query": request.query,
        "answer": answer,
        "context_length": len(context)
    }


@router.get("/status")
async def rag_status():
    return {
        "rag_enabled": True,
        "llm_enabled": True,
        "document_retrieval": True,
        "semantic_search": True
    }