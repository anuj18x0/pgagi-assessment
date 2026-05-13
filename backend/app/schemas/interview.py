from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

class ContextSource(BaseModel):
    source: str
    text: str
    score: float

class GeneratedQuestion(BaseModel):
    question_text: str = Field(description="The technical question text")
    suggested_answer_outline: List[str] = Field(description="Key points that should be in the candidate's answer")
    difficulty_level: str = Field(description="Junior/Mid/Senior")
    context_used: List[ContextSource] = Field(description="Context chunks used to ground the question")

class QuestionGenerationRequest(BaseModel):
    session_id: UUID
    role: str
    skills: List[str]
