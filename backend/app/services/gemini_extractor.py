from google import genai
from typing import List, Dict, Any, Optional
import json
import logging
from pydantic import ValidationError
from app.schemas.resume import ExtractedSkills
from app.core.config import settings

logger = logging.getLogger(__name__)

class GeminiExtractor:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY must be provided")
        self.client = genai.Client(api_key=self.api_key)
        self.model_id = "gemini-2.0-flash"

    async def extract_skills(self, text: str) -> ExtractedSkills:
        """
        Extract skills, technologies, experience, and domains from resume text using Gemini.
        """
        prompt = f"""
        You are an expert recruitment AI. Extract the following information from the resume text provided below.
        Return ONLY a structured JSON object matching this schema:
        {{
            "skills": ["general skills"],
            "technologies": ["tech stack, languages, tools"],
            "years_experience": integer or null,
            "domains": ["industry domains, specializations"]
        }}

        Resume Text:
        ---
        {text}
        ---

        Few-shot examples:
        Input: "Software Engineer with 5 years experience in Python and AWS. Specialized in Fintech."
        Output: {{ "skills": ["Software Engineering"], "technologies": ["Python", "AWS"], "years_experience": 5, "domains": ["Fintech"] }}
        """

        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config={
                    "response_mime_type": "application/json"
                }
            )
            
            data = json.loads(response.text)
            return ExtractedSkills(**data)
        except (ValidationError, json.JSONDecodeError) as e:
            logger.error(f"Failed to parse Gemini response: {e}")
            # Fallback for poor resumes or parsing errors
            return ExtractedSkills(skills=[], technologies=[], years_experience=0, domains=[])
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise

    def infer_domain(self, extracted: ExtractedSkills) -> str:
        """
        Classify candidate into ML, Backend, Data, or Fullstack based on skills/tech.
        """
        techs = [t.lower() for t in extracted.technologies]
        skills = [s.lower() for s in extracted.skills]
        all_indicators = techs + skills

        if any(kw in all_indicators for kw in ["pytorch", "tensorflow", "scikit-learn", "ml", "nlp", "computer vision"]):
            return "ML Engineer"
        if any(kw in all_indicators for kw in ["django", "flask", "fastapi", "go", "java", "spring", "sql", "postgres"]):
            return "Backend Developer"
        if any(kw in all_indicators for kw in ["react", "vue", "angular", "css", "html", "javascript", "typescript", "frontend"]):
            if "Backend Developer" in self.infer_domain(extracted): # Simple check for fullstack
                return "Fullstack Developer"
            return "Fullstack Developer" # Defaulting for now if web-heavy
        if any(kw in all_indicators for kw in ["spark", "hadoop", "airflow", "data engineering", "etl"]):
            return "Data Engineer"
            
        return "Software Engineer"

    def build_rag_queries(self, extracted: ExtractedSkills, role: str) -> List[str]:
        """
        Translate extracted skills into targeted RAG queries.
        """
        queries = [f"Core {role} interview questions and fundamentals"]
        
        # Add tech-specific queries
        for tech in extracted.technologies[:2]:
            queries.append(f"Applied {tech} concepts and advanced questions for {role}")
            
        # Add skill-specific queries
        for skill in extracted.skills[:1]:
            queries.append(f"{skill} best practices and scenario-based questions")

        # Fallback for poor resumes
        if len(extracted.skills) < 3 and len(extracted.technologies) < 3:
            logger.warning("Poor resume detected, using fallback queries")
            queries.append(f"Standard {role} technical interview preparation")
            
        return list(set(queries))[:5]
