# ==================================================
# NEXORA AI — FILE UPLOAD ROUTES
# POST /api/files/upload  — upload + process file
# POST /api/files/query   — ask question about file
# GET  /api/files/list    — list user's files
# ==================================================

import os
import shutil
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel

from app.agents.file_agent import FileAgent
from app.database.database import AsyncSessionLocal
from app.database.models import UploadedDocument
from sqlalchemy import select
from datetime import datetime

router = APIRouter()
file_agent = FileAgent()

UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".txt", ".md",
    ".csv", ".xlsx", ".xls",
    ".png", ".jpg", ".jpeg", ".webp"
}


# ==================================================
# UPLOAD + PROCESS FILE
# ==================================================

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    query: Optional[str] = Form(None),
    store_in_rag: bool = Form(True)
):

    # Validate extension
    ext = os.path.splitext(file.filename)[-1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. "
                   f"Supported: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Save file to disk
    safe_name = f"{user_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_name)

    try:
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save file: {str(e)}"
        )

    # Process file with FileAgent
    result = await file_agent.run(
        file_path=file_path,
        query=query,
        user_id=user_id,
        store_in_rag=store_in_rag
    )

    # Save record to PostgreSQL
    try:
        async with AsyncSessionLocal() as db:
            doc = UploadedDocument(
                user_id=user_id,
                filename=file.filename,
                file_type=ext.replace(".", ""),
                extracted_text=result.get("summary", ""),
                created_at=datetime.utcnow()
            )
            db.add(doc)
            await db.commit()
    except Exception as e:
        print(f"[FileRoutes] DB save error: {e}")

    return {
        "success": result.get("success"),
        "file_name": file.filename,
        "file_type": ext,
        "summary": result.get("summary"),
        "text_length": result.get("text_length"),
        "chunk_count": result.get("chunk_count"),
        "rag_stored": result.get("rag_stored"),
        "execution_time": result.get("execution_time"),
        "error": result.get("error")
    }


# ==================================================
# QUERY AN ALREADY-UPLOADED FILE
# ==================================================

class FileQueryRequest(BaseModel):
    user_id: str
    file_name: str
    query: str


@router.post("/query")
async def query_file(request: FileQueryRequest):

    file_path = os.path.join(
        UPLOAD_DIR,
        request.file_name
    )

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail=f"File '{request.file_name}' not found"
        )

    result = await file_agent.run(
        file_path=file_path,
        query=request.query,
        user_id=request.user_id,
        store_in_rag=False
    )

    return {
        "success": result.get("success"),
        "file_name": request.file_name,
        "query": request.query,
        "answer": result.get("summary"),
        "error": result.get("error")
    }


# ==================================================
# LIST USER'S UPLOADED FILES
# ==================================================

@router.get("/list/{user_id}")
async def list_files(user_id: str):

    try:

        async with AsyncSessionLocal() as db:

            stmt = select(UploadedDocument).where(
                UploadedDocument.user_id == user_id
            )

            result = await db.execute(stmt)
            docs = result.scalars().all()

            return {
                "success": True,
                "user_id": user_id,
                "files": [
                    {
                        "id": doc.id,
                        "filename": doc.filename,
                        "file_type": doc.file_type,
                        "created_at": str(doc.created_at)
                    }
                    for doc in docs
                ],
                "count": len(docs)
            }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }