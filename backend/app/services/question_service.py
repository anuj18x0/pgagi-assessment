import json
import logging
from typing import List, Dict, Any
from uuid import UUID
from app.core.config import settings
from app.rag.service import RAGService, ContextChunk
from app.schemas.interview import GeneratedQuestion, ContextSource
from app.services.gemini_service import GeminiService
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

class QuestionService:
    def __init__(self, api_key: str = None, redis_client: aioredis.Redis = None):
        self.gemini = GeminiService(api_key=api_key)
        self.rag_service = RAGService()
        self.redis = redis_client
        self.model_id = "gemini-2.5-flash"
        self.config = {
            "temperature": 0.7,
            "max_tokens": 300,
            "top_p": 0.9
        }

    async def _get_prior_questions(self, session_id: UUID) -> List[str]:
        """Retrieve list of already asked questions from Redis."""
        if not self.redis:
            return []
        key = f"interview:{session_id}:questions"
        data = await self.redis.get(key)
        return json.loads(data) if data else []

    async def _track_question(self, session_id: UUID, question_text: str):
        """Store asked question in Redis to prevent repetition."""
        if not self.redis:
            return
        key = f"interview:{session_id}:questions"
        prior = await self._get_prior_questions(session_id)
        prior.append(question_text)
        await self.redis.set(key, json.dumps(prior), ex=3600)

    def _determine_tier(self, years_exp: int, domain_match: bool) -> str:
        """Calibrate difficulty based on seniority."""
        if years_exp >= 8 and domain_match:
            return "Architectural"
        if years_exp >= 3:
            return "Applied"
        return "Foundational"

    async def generate_technical_question(
        self, 
        role: str, 
        skills: List[str], 
        session_id: UUID,
        years_exp: int = 0,
        domain_match: bool = True
    ) -> GeneratedQuestion:
        """
        Orchestrate context retrieval and grounded question generation with diversity tracking.
        """
        # 1. Retrieve RAG context
        context_chunks = await self.rag_service.retrieve_context(skills, role)
        context_text = "\n\n".join([f"Source: {c.source}\nContent: {c.text}" for c in context_chunks])
        
        # 2. Get prior questions for diversity
        prior_questions = await self._get_prior_questions(session_id)
        prior_text = "\n".join([f"- {q}" for q in prior_questions])
        
        # 3. Calibrate difficulty
        tier = self._determine_tier(years_exp, domain_match)
        
        # 4. Generate grounded question
        system_prompt = f"You are a senior {role} interviewer. Generate a technical question grounded in the context below. Do NOT be generic. Reference specific concepts from the text."
        
        user_prompt = f"""
        CONTEXT FROM TECHNICAL DOCUMENTATION:
        ---
        {context_text}
        ---

        CANDIDATE PROFILE:
        - Skills: {', '.join(skills)}
        - Seniority Tier: {tier}

        ALREADY ASKED QUESTIONS (DO NOT REPEAT):
        {prior_text}

        TASK:
        Generate a {tier} level technical interview question that:
        1. Is grounded SPECIFICALLY in the provided context.
        2. Avoids repeating any concepts from the already asked questions.
        3. Tests technical depth appropriate for the '{tier}' tier.
        4. Includes a brief outline of the expected correct answer.

        Return ONLY a JSON object matching this schema:
        {{
            "question_text": "string",
            "suggested_answer_outline": ["point 1", "point 2"],
            "difficulty_level": "{tier}"
        }}
        """

        try:
            data = await self.gemini.generate_json(
                prompt=user_prompt,
                system_instruction=system_prompt,
                model_id=self.model_id,
                **self.config
            )
            
            # Track for diversity
            await self._track_question(session_id, data["question_text"])
            
            return GeneratedQuestion(
                question_text=data["question_text"],
                suggested_answer_outline=data["suggested_answer_outline"],
                difficulty_level=data["difficulty_level"],
                context_used=[
                    ContextSource(source=c.source, text=c.text, score=c.score)
                    for c in context_chunks
                ]
            )
        except Exception as e:
            logger.error(f"Question generation failed: {e}")
            raise
