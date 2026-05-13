from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis
from uuid import UUID
from pydantic import BaseModel
import json

from app.core.dependencies import get_db, get_redis
from app.schemas.interview import GeneratedQuestion, QuestionGenerationRequest
from app.services.interview_service import InterviewService

router = APIRouter(prefix="/interview", tags=["interview"])

class AnswerSubmission(BaseModel):
    session_id: UUID
    question_id: UUID
    answer_text: str

@router.post("/start/{session_id}", status_code=status.HTTP_200_OK)
async def start_interview(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis)
):
    """Start the interview and pre-plan question slots."""
    service = InterviewService(db, redis)
    try:
        await service.start_interview(session_id)
        await db.commit()
        return {"message": "Interview started"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/next-question", response_model=GeneratedQuestion)
async def get_next_question(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis)
):
    """Generate and return the next question."""
    service = InterviewService(db, redis)
    try:
        question = await service.get_next_question(session_id)
        if not question:
            return JSONResponse(status_code=204, content={"message": "Interview complete"})
        await db.commit()
        return question
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/answer")
async def submit_answer(
    submission: AnswerSubmission,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis)
):
    """Submit an answer to a question."""
    service = InterviewService(db, redis)
    try:
        result = await service.submit_answer(
            submission.session_id, submission.question_id, submission.answer_text
        )
        await db.commit()
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{session_id}/summary")
async def get_summary(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis)
):
    """Generate or retrieve the interview summary."""
    service = InterviewService(db, redis)
    
    # Check cache
    cached = await redis.get(f"interview:{session_id}:summary")
    if cached:
        return json.loads(cached)
        
    try:
        summary = await service.generate_summary(session_id)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {str(e)}")
