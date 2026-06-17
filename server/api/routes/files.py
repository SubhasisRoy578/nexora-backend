"""
Nexora AI — File Upload Router
Handles file uploads, triggers RAG processing, and manages user documents.
Supports PDF, DOCX, TXT, CSV, XLSX, images, code files.
"""

import os
import uuid
import shutil
from pathlib import Path
from datetime import datetime
from typing import List

from fastapi import (
    APIRouter, Depends, HTTPException, UploadFile,
    File, BackgroundTasks, status,
)
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import aiofiles

from app.config import settings
from app.database import get_postgres_db
from app.models.file import UploadedFile, FileStatus
from app.models.user import User
from app.schemas.schemas import FileUploadResponse, FileListResponse, FileProcessingStatus
from app.services.rag.rag_pipeline import RAGPipeline
from app.middleware.auth_middleware import get_current_user

router = APIRouter()
rag_pipeline = RAGPipeline()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".txt", ".md",
    ".csv", ".xlsx", ".xls",
    ".py", ".js", ".ts", ".json", ".yaml", ".yml",
    ".png", ".jpg", ".jpeg", ".webp",
}

MAX_FILE_SIZE = settings.MAX_FILE_SIZE_MB * 1024 * 1024


async def _process_file_background(
    file_id: str,
    file_path: str,
    user_id: str,
    filename: str,
    db_session_factory,
):
    """Background task: run RAG processing after upload."""
    from app.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        try:
            result = await rag_pipeline.process_document(
                file_path=file_path,
                user_id=user_id,
                file_id=file_id,
                filename=filename,
            )

            # Update file status
            q = await db.execute(
                select(UploadedFile).where(UploadedFile.id == uuid.UUID(file_id))
            )
            file_record = q.scalar_one_or_none()
            if file_record:
                file_record.status = FileStatus.READY
                file_record.chunk_count = result["chunks"]
                file_record.processed_at = datetime.utcnow()
                file_record.extracted_text_preview = f"Processed {result['chars']} chars into {result['chunks']} chunks"
                await db.commit()

        except Exception as e:
            q = await db.execute(
                select(UploadedFile).where(UploadedFile.id == uuid.UUID(file_id))
            )
            file_record = q.scalar_one_or_none()
            if file_record:
                file_record.status = FileStatus.FAILED
                file_record.processing_error = str(e)[:500]
                await db.commit()


@router.post("/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_postgres_db),
):
    """
    Upload a file and trigger async RAG processing.
    The file is immediately available for reference; RAG indexing runs in background.
    """
    # Validate extension
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type '{suffix}' not supported. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Validate size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {settings.MAX_FILE_SIZE_MB}MB limit",
        )

    # Save to disk
    file_id = str(uuid.uuid4())
    stored_filename = f"{file_id}{suffix}"
    file_path = UPLOAD_DIR / stored_filename

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    # Create DB record
    db_file = UploadedFile(
        id=uuid.UUID(file_id),
        user_id=current_user.id,
        original_filename=file.filename or stored_filename,
        stored_filename=stored_filename,
        content_type=file.content_type or "application/octet-stream",
        file_size_bytes=len(content),
        storage_provider="local",
        storage_path=str(file_path),
        status=FileStatus.PROCESSING,
        vector_namespace=f"docs:{current_user.id}",
    )
    db.add(db_file)
    await db.commit()
    await db.refresh(db_file)

    # Queue RAG processing
    background_tasks.add_task(
        _process_file_background,
        file_id=file_id,
        file_path=str(file_path),
        user_id=str(current_user.id),
        filename=file.filename or stored_filename,
        db_session_factory=None,
    )

    return db_file


@router.get("/", response_model=FileListResponse)
async def list_files(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_postgres_db),
):
    """List all uploaded files for the current user."""
    from sqlalchemy import func

    result = await db.execute(
        select(UploadedFile)
        .where(UploadedFile.user_id == current_user.id)
        .order_by(UploadedFile.created_at.desc())
        .offset(offset).limit(limit)
    )
    files = result.scalars().all()

    count_result = await db.execute(
        select(func.count(UploadedFile.id))
        .where(UploadedFile.user_id == current_user.id)
    )
    total = count_result.scalar()

    return {"files": files, "total": total}


@router.get("/{file_id}/status", response_model=FileProcessingStatus)
async def get_file_status(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_postgres_db),
):
    """Check the processing status of an uploaded file."""
    result = await db.execute(
        select(UploadedFile).where(
            UploadedFile.id == uuid.UUID(file_id),
            UploadedFile.user_id == current_user.id,
        )
    )
    file_record = result.scalar_one_or_none()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    return {
        "file_id": str(file_record.id),
        "filename": file_record.original_filename,
        "status": file_record.status.value,
        "chunk_count": file_record.chunk_count,
        "error": file_record.processing_error,
    }


@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_postgres_db),
):
    """Delete a file and remove its vectors from the index."""
    result = await db.execute(
        select(UploadedFile).where(
            UploadedFile.id == uuid.UUID(file_id),
            UploadedFile.user_id == current_user.id,
        )
    )
    file_record = result.scalar_one_or_none()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    # Delete from disk
    try:
        os.remove(file_record.storage_path)
    except FileNotFoundError:
        pass

    # Delete from DB
    await db.delete(file_record)
    await db.commit()

    return {"success": True, "file_id": file_id}