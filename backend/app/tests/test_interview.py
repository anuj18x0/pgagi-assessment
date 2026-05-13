import pytest
from httpx import AsyncClient
from unittest.mock import MagicMock, patch
from uuid import uuid4
import json

from app.services.question_service import QuestionService
from app.schemas.interview import GeneratedQuestion

@pytest.mark.asyncio
async def test_question_generation_logic():
    """
    Unit test for question generation grounding.
    """
    service = QuestionService(api_key="fake_key")
    
    mock_context = [
        MagicMock(source="Book.pdf", text="Python decorators are powerful.", score=0.9)
    ]
    
    with patch.object(service.rag_service, 'retrieve_context', return_value=mock_context):
        with patch.object(service.client.models, 'generate_content') as mock_gen:
            mock_gen.return_value.text = json.dumps({
                "question_text": "How do decorators work in Python?",
                "suggested_answer_outline": ["First class functions", "Wrappers"],
                "difficulty_level": "Mid"
            })
            
            result = await service.generate_technical_question("Software Engineer", ["Python"])
            
            assert "decorators" in result.question_text.lower()
            assert result.difficulty_level == "Mid"
            assert len(result.context_used) == 1

@pytest.mark.asyncio
async def test_generate_endpoint_error_handling(client: AsyncClient):
    """
    Test 404 if session doesn't exist.
    """
    data = {
        "session_id": str(uuid4()),
        "role": "Software Engineer",
        "skills": ["Python"]
    }
    
    response = await client.post("/api/v1/interview/generate", json=data)
    assert response.status_code == 404
