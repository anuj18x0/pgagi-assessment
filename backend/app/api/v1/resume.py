from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, status
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from app.core.dependencies import get_db, get_redis
from app.services.resume_service import ResumeService
from app.schemas.resume import ResumeResponse
from app.core.config import settings

router = APIRouter(prefix="/resume", tags=["resume"])

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

@router.post("/upload", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    session_id: UUID = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis)
):
    """
    Upload and process a candidate's resume (PDF or TXT).
    Validates MIME type and file size.
    """
    # Validate MIME type
    if file.content_type not in ["application/pdf", "text/plain"]:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF and TXT files are allowed"
        )

    # Validate file size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds 5MB limit"
        )

    # Validate Magic Bytes for PDF
    if file.content_type == "application/pdf":
        if not content.startswith(b"%PDF"):
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Invalid PDF file signature"
            )

    service = ResumeService(db, redis)
    try:
        resume_data = await service.process_resume(
            content, session_id, file.filename, file.content_type
        )
        await db.commit()
        return resume_data
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resume processing failed: {str(e)}"
        )
