import os
import shutil
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.simplified_rag import save_document

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".csv"}


@router.post("/")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a file, extract text, chunk it, embed it, and store in database."""
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    safe_name = file.filename.replace(" ", "_")
    file_path = os.path.join(UPLOAD_DIR, safe_name)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File save error: {e}")

    file_size = os.path.getsize(file_path)

    # Process, chunk, embed and index document
    try:
        num_chunks = save_document(db, file_path, safe_name)
    except Exception as e:
        # Clean up file on failure
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Indexing error: {e}")

    return {
        "success": True,
        "filename": safe_name,
        "size_bytes": file_size,
        "uploaded_at": str(datetime.utcnow()),
        "chunks_indexed": num_chunks,
        "message": f"Document indexed into database ({num_chunks} chunks)"
    }


@router.get("/files")
async def list_files(db: Session = Depends(get_db)):
    """List all indexed documents and chunk counts."""
    from app.models.document import DocumentChunk
    from sqlalchemy import func

    results = (
        db.query(DocumentChunk.filename, func.count(DocumentChunk.id).label("chunks"))
        .group_by(DocumentChunk.filename)
        .all()
    )
    return {
        "files": [{"filename": r.filename, "chunks": r.chunks} for r in results]
    }


@router.delete("/files/{filename}")
async def delete_file(filename: str, db: Session = Depends(get_db)):
    """Delete a document's chunks from database and disk."""
    from app.models.document import DocumentChunk

    deleted = db.query(DocumentChunk).filter(DocumentChunk.filename == filename).delete()
    db.commit()

    file_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    return {"success": True, "deleted_chunks": deleted, "filename": filename}