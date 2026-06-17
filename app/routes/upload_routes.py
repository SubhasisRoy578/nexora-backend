from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException
)
from datetime import datetime
import os
import shutil
from app.simplified_rag import save_document

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(
    UPLOAD_DIR,
    exist_ok=True
)


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...)
):
    try:
        file_path = os.path.join(
            UPLOAD_DIR,
            file.filename
        )

        with open(
            file_path,
            "wb"
        ) as buffer:
            shutil.copyfileobj(
                file.file,
                buffer
            )

        file_size = os.path.getsize(
            file_path
        )

        # Process and index document using simplified RAG
        num_chunks = save_document(file_path, file.filename)

        return {
            "success": True,
            "filename": file.filename,
            "size_bytes": file_size,
            "uploaded_at": str(datetime.utcnow()),
            "chunks": num_chunks,
            "indexed": True,
            "message": "Document uploaded and indexed into simplified RAG"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )