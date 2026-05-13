from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

class ExtractedSkills(BaseModel):
    skills: List[str] = Field(description="List of general skills, e.g., 'Project Management', 'Agile'")
    technologies: List[str] = Field(description="List of specific technologies, programming languages, or tools, e.g., 'Python', 'React', 'Docker'")
    years_experience: Optional[int] = Field(default=None, description="Total years of professional experience, if stated or deducible")
    domains: List[str] = Field(description="List of industry domains or specializations, e.g., 'Finance', 'Machine Learning', 'E-commerce'")

class ResumeResponse(BaseModel):
    id: UUID
    session_id: UUID
    domain: str
    extracted_skills: ExtractedSkills
    file_hash: str
    s3_url: Optional[str] = None
