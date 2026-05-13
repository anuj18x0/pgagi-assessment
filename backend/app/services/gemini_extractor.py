from typing import List, Dict, Any, Optional
import logging
from app.schemas.resume import ExtractedSkills
from app.services.gemini_service import GeminiService

logger = logging.getLogger(__name__)

class GeminiExtractor:
    def __init__(self):
        self.gemini = GeminiService()
        self.model_id = "gemini-2.5-flash"

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
            data = await self.gemini.generate_json(
                prompt=prompt,
                model_id=self.model_id
            )
            return ExtractedSkills(**data)
        except Exception as e:
            logger.error(f"Failed to extract skills: {e}")
            # Fallback for poor resumes or parsing errors
            return ExtractedSkills(skills=[], technologies=[], years_experience=0, domains=[])

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
            return "Fullstack Developer"
        if any(kw in all_indicators for kw in ["spark", "hadoop", "airflow", "data engineering", "etl"]):
            return "Data Engineer"
            
        return "Software Engineer"

    def build_rag_queries(self, extracted: ExtractedSkills, role: str) -> List[str]:
        """
        Translate extracted skills into targeted RAG queries.
        """
        queries = [f"Core {role} interview questions and fundamentals"]
        
        for tech in extracted.technologies[:2]:
            queries.append(f"Applied {tech} concepts and advanced questions for {role}")
            
        for skill in extracted.skills[:1]:
            queries.append(f"{skill} best practices and scenario-based questions")

        if len(extracted.skills) < 3 and len(extracted.technologies) < 3:
            logger.warning("Poor resume detected, using fallback queries")
            queries.append(f"Standard {role} technical interview preparation")
            
        return list(set(queries))[:5]
