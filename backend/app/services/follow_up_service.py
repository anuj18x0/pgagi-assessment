import json
import logging
from typing import Optional, Dict, Any
from google import genai
from app.core.config import settings

logger = logging.getLogger(__name__)

class FollowUpService:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.client = genai.Client(api_key=self.api_key)
        self.model_id = "gemini-2.5-flash"

    async def analyze_answer_and_generate_followup(
        self, 
        question: str, 
        answer: str, 
        context: str
    ) -> Optional[str]:
        """
        Analyze candidate's answer. If shallow or missing details, generate a follow-up.
        """
        prompt = f"""
        You are an expert technical interviewer.
        
        Original Question: {question}
        Documentation Context: {context}
        Candidate's Answer: {answer}
        
        TASK:
        1. Evaluate if the answer is "complete" or "shallow/evasive".
        2. If the answer is shallow or misses key technical nuances mentioned in the context, generate a brief, targeted follow-up question to probe deeper.
        3. If the answer is comprehensive, return null.
        
        Return ONLY a JSON object:
        {{
            "is_shallow": boolean,
            "follow_up_question": "string or null",
            "reasoning": "brief explanation"
        }}
        """

        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "temperature": 0.5
                }
            )
            
            data = json.loads(response.text)
            if data.get("is_shallow") and data.get("follow_up_question"):
                return data["follow_up_question"]
            return None
        except Exception as e:
            logger.error(f"Follow-up generation failed: {e}")
            return None
