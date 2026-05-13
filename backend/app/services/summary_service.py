import logging
from typing import List, Dict, Any
from app.services.gemini_service import GeminiService

logger = logging.getLogger(__name__)

class SummaryService:
    def __init__(self):
        self.gemini = GeminiService()

    async def summarize_interview(self, qa_pairs: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Generate a comprehensive summary of an interview session.
        """
        if not qa_pairs:
            return {
                "topics": [],
                "observations": "No questions were answered.",
                "growth_areas": []
            }

        qa_text = "\n\n".join([f"Q: {pair['question']}\nA: {pair['answer']}" for pair in qa_pairs])
        
        prompt = f"""
        Analyze the following technical interview transcript.
        Transcript:
        {qa_text}
        
        Provide a structured evaluation in JSON format:
        {{
            "topics": ["list of technical topics discussed"],
            "observations": "Detailed analysis of the candidate's performance, technical depth, and communication style.",
            "growth_areas": ["specific areas where the candidate could improve based on their answers"]
        }}
        """

        try:
            summary = await self.gemini.generate_json(
                prompt=prompt,
                system_instruction="You are a principal engineer conducting a post-interview debrief.",
                model_id="gemini-2.5-flash"
            )
            return summary
        except Exception as e:
            logger.error(f"Interview summarization failed: {e}")
            raise
