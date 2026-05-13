import pytest
from httpx import AsyncClient
from unittest.mock import MagicMock, patch
from uuid import uuid4
import json

from app.services.gemini_extractor import GeminiExtractor
from app.schemas.resume import ExtractedSkills

@pytest.fixture
def mock_gemini_response():
    return ExtractedSkills(
        skills=["Software Engineering", "Agile"],
        technologies=["Python", "FastAPI", "Docker"],
        years_experience=5,
        domains=["Backend", "Cloud"]
    )

@pytest.mark.asyncio
async def test_gemini_extraction_logic(mock_gemini_response):
    """
    Unit test for Gemini extraction and domain inference.
    """
    extractor = GeminiExtractor()
    
    with patch.object(extractor.client.models, 'generate_content') as mock_gen:
        mock_gen.return_value.text = json.dumps(mock_gemini_response.model_dump())
        
        result = await extractor.extract_skills("Fake resume text")
        
        assert result.skills == ["Software Engineering", "Agile"]
        assert result.technologies == ["Python", "FastAPI", "Docker"]
        
        domain = extractor.infer_domain(result)
        assert domain == "Backend Developer"

@pytest.mark.asyncio
async def test_rag_query_builder():
    extractor = GeminiExtractor()
    extracted = ExtractedSkills(
        skills=["Distributed Systems"],
        technologies=["Kafka", "Go"],
        years_experience=3,
        domains=["Fintech"]
    )
    
    queries = extractor.build_rag_queries(extracted, "Backend Developer")
    assert len(queries) >= 3
    assert any("Kafka" in q for q in queries)
    assert any("Go" in q for q in queries)

@pytest.mark.asyncio
async def test_upload_resume_endpoint(client: AsyncClient, db_session):
    """
    Integration test for resume upload.
    """
    session_id = uuid4()
    # Create a mock session in DB if needed, but for now we test the endpoint validation
    
    # Valid PDF upload
    pdf_content = b"%PDF-1.4\nTest PDF content"
    files = {"file": ("resume.pdf", pdf_content, "application/pdf")}
    data = {"session_id": str(session_id)}
    
    with patch("app.services.resume_service.ResumeService.process_resume") as mock_process:
        mock_process.return_value = MagicMock(
            id=uuid4(),
            session_id=session_id,
            domain="Backend Developer",
            extracted_skills={"skills": ["Python"]},
            file_hash="abc",
            s3_url="http://s3.com/resume.pdf"
        )
        
        response = await client.post("/api/v1/resume/upload", data=data, files=files)
        
        assert response.status_code == 201
        assert response.json()["domain"] == "Backend Developer"

@pytest.mark.asyncio
async def test_upload_invalid_mime(client: AsyncClient):
    files = {"file": ("resume.exe", b"fake binary", "application/x-msdownload")}
    data = {"session_id": str(uuid4())}
    
    response = await client.post("/api/v1/resume/upload", data=data, files=files)
    assert response.status_code == 415
    assert "Only PDF and TXT files are allowed" in response.json()["detail"]

@pytest.mark.asyncio
async def test_upload_size_limit(client: AsyncClient):
    large_content = b"a" * (6 * 1024 * 1024) # 6MB
    files = {"file": ("large.pdf", large_content, "application/pdf")}
    data = {"session_id": str(uuid4())}
    
    response = await client.post("/api/v1/resume/upload", data=data, files=files)
    assert response.status_code == 413
