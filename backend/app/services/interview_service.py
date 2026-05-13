import json
import logging
from uuid import UUID
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from app.models.session import SessionStatus, Session
from app.repositories.session_repo import SessionRepository
from app.repositories.question_repo import QuestionRepository
from app.repositories.answer_repo import AnswerRepository
from app.repositories.resume_repo import ResumeRepository
from app.services.question_service import QuestionService
from app.services.interview_planner import InterviewPlanner
from app.services.follow_up_service import FollowUpService
from google import genai
from app.core.config import settings

logger = logging.getLogger(__name__)

class InterviewService:
    def __init__(self, db: AsyncSession, redis: aioredis.Redis):
        self.db = db
        self.redis = redis
        self.session_repo = SessionRepository(db)
        self.question_repo = QuestionRepository(db)
        self.answer_repo = AnswerRepository(db)
        self.resume_repo = ResumeRepository(db)
        self.question_service = QuestionService(redis_client=redis)
        self.follow_up_service = FollowUpService()

    async def get_state(self, session_id: UUID) -> Dict[str, Any]:
        key = f"interview:{session_id}:state"
        data = await self.redis.get(key)
        return json.loads(data) if data else {}

    async def update_state(self, session_id: UUID, updates: Dict[str, Any]):
        state = await self.get_state(session_id)
        state.update(updates)
        await self.redis.set(f"interview:{session_id}:state", json.dumps(state), ex=86400)

    async def transition_state(self, session_id: UUID, target_status: SessionStatus):
        """Enforce server-side state transitions."""
        session = await self.session_repo.get(session_id)
        if not session:
            raise ValueError("Session not found")

        valid_transitions = {
            SessionStatus.CREATED: [SessionStatus.RESUME_UPLOADED, SessionStatus.CANCELLED],
            SessionStatus.RESUME_UPLOADED: [SessionStatus.STARTED, SessionStatus.CANCELLED],
            SessionStatus.STARTED: [SessionStatus.IN_PROGRESS, SessionStatus.CANCELLED],
            SessionStatus.IN_PROGRESS: [SessionStatus.COMPLETED, SessionStatus.CANCELLED],
        }

        if target_status not in valid_transitions.get(session.status, []):
            raise ValueError(f"Invalid transition from {session.status} to {target_status}")

        await self.session_repo.update(session_id, status=target_status)
        await self.update_state(session_id, {"status": target_status})

    async def start_interview(self, session_id: UUID):
        """Pre-plan the interview slots and start."""
        await self.transition_state(session_id, SessionStatus.STARTED)
        
        planner = InterviewPlanner()
        plan = [p.value for p in planner.plan_session()]
        await self.update_state(session_id, {
            "plan": plan,
            "current_index": 0,
            "status": SessionStatus.STARTED.value
        })
        
        await self.transition_state(session_id, SessionStatus.IN_PROGRESS)

    async def get_next_question(self, session_id: UUID):
        """Generate and store the next question based on plan."""
        state = await self.get_state(session_id)
        if state.get("status") != SessionStatus.IN_PROGRESS.value:
            raise ValueError("Interview is not in progress")

        session = await self.session_repo.get(session_id)
        resume = await self.resume_repo.get_by_session(session_id)
        
        plan = state.get("plan", [])
        index = state.get("current_index", 0)
        
        if index >= len(plan):
            await self.transition_state(session_id, SessionStatus.COMPLETED)
            return None

        # Determine category and generate
        # In a real app, we'd use the planner category to modify the prompt
        # but here we'll use our enhanced QuestionService
        generated = await self.question_service.generate_technical_question(
            role=session.selected_role,
            skills=resume.extracted_skills.get("skills", []),
            session_id=session_id,
            years_exp=resume.extracted_skills.get("years_experience", 0)
        )
        
        # Store in DB
        await self.question_repo.create(
            session_id=session_id,
            question_text=generated.question_text,
            retrieved_context=json.dumps([c.model_dump() for c in generated.context_used]),
            order_index=index
        )
        
        await self.update_state(session_id, {"current_index": index + 1})
        return generated

    async def submit_answer(self, session_id: UUID, question_id: UUID, answer_text: str):
        """Submit answer, log it, and check for follow-up."""
        state = await self.get_state(session_id)
        if state.get("status") != SessionStatus.IN_PROGRESS.value:
            raise ValueError("Interview is not in progress")

        # Store answer
        await self.answer_repo.create(
            session_id=session_id,
            question_id=question_id,
            answer_text=answer_text,
            word_count=len(answer_text.split())
        )
        
        # Optional: Follow-up logic could be triggered here
        # For now, we just proceed
        return {"status": "success"}

    async def generate_summary(self, session_id: UUID):
        """Generate a summary of the interview via Gemini."""
        # 1. Fetch all Q&A
        questions = await self.question_repo.get_by_session(session_id)
        answers = await self.answer_repo.get_by_session(session_id)
        
        qa_pairs = []
        for q in questions:
            a = next((ans for ans in answers if ans.question_id == q.id), None)
            if a:
                qa_pairs.append(f"Q: {q.question_text}\nA: {a.answer_text}")

        qa_text = "\n\n".join(qa_pairs)
        
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        prompt = f"""
        Summarize the following technical interview Q&A pairs.
        Provide:
        1. Topics covered.
        2. Observations on answer quality (depth, correctness).
        3. Suggested areas for growth for the candidate.
        
        Interview Text:
        {qa_text}
        
        Return ONLY a JSON object:
        {{
            "topics": ["topic1", "topic2"],
            "observations": "string",
            "growth_areas": ["area1", "area2"]
        }}
        """

        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config={"response_mime_type": "application/json"}
            )
            summary_data = json.loads(response.text)
            
            # Cache in Redis
            await self.redis.set(f"interview:{session_id}:summary", json.dumps(summary_data), ex=86400)
            return summary_data
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            raise
