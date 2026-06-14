from fastapi import APIRouter, UploadFile, File, HTTPException
from datetime import datetime
import os
import shutil

from ..rag.document_processor import DocumentProcessor
from ..rag.ingest import process_document

router = APIRouter()

processor = DocumentProcessor()
UPLOAD_DIR = "uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_size = os.path.getsize(file_path)

        processed = await processor.process_document(file_path)

        rag_result = process_document(
            text=processed["text"],
            source_file=file.filename
        )

        return {
            "success": True,
            "filename": file.filename,
            "size_bytes": file_size,
            "uploaded_at": str(datetime.utcnow()),
            "chunks": rag_result["chunks"],
            "indexed": rag_result["indexed"],
            "message": "Document uploaded and indexed into RAG"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
