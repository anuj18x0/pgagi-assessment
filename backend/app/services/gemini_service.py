import json
import logging
from typing import Any, Dict, List, Optional
from google import genai
from app.core.config import settings

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY must be provided")
        self.client = genai.Client(api_key=self.api_key)

    async def generate_json(
        self, 
        prompt: str, 
        system_instruction: Optional[str] = None,
        model_id: str = "gemini-2.5-flash",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        top_p: float = 0.9
    ) -> Dict[str, Any]:
        """
        Generic method to generate structured JSON from Gemini.
        """
        try:
            config = {
                "response_mime_type": "application/json",
                "temperature": temperature,
                "max_output_tokens": max_tokens,
                "top_p": top_p
            }
            if system_instruction:
                config["system_instruction"] = system_instruction

            response = self.client.models.generate_content(
                model=model_id,
                contents=prompt,
                config=config
            )
            
            return json.loads(response.text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode Gemini JSON: {e}")
            raise
        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            raise

    async def generate_text(
        self, 
        prompt: str, 
        system_instruction: Optional[str] = None,
        model_id: str = "gemini-2.0-flash"
    ) -> str:
        """
        Generic method to generate plain text from Gemini.
        """
        try:
            config = {}
            if system_instruction:
                config["system_instruction"] = system_instruction

            response = self.client.models.generate_content(
                model=model_id,
                contents=prompt,
                config=config
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini text generation error: {e}")
            raise
