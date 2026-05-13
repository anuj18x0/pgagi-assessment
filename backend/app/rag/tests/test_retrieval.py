import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4
from app.rag.service import RAGService, ContextChunk

@pytest.fixture
def mock_embedder():
    with patch("rag.service.GoogleEmbedder") as mock:
        instance = mock.return_value
        instance.embed_query.return_value = [0.1] * 768
        instance.client = MagicMock()
        yield instance

@pytest.fixture
def mock_vectorstore():
    with patch("rag.service.PineconeStore") as mock:
        instance = mock.return_value
        # Mock Pinecone query result
        mock_match = MagicMock()
        mock_match.id = str(uuid4())
        mock_match.score = 0.85
        mock_match.metadata = {
            "text": "This is a test chunk of context about Python fundamentals.",
            "source_book": "Python Mastery.pdf",
            "page_range": "10-12"
        }
        
        mock_query_result = MagicMock()
        mock_query_result.matches = [mock_match]
        instance.query.return_value = mock_query_result
        yield instance

@pytest.fixture
def mock_reranker():
    with patch("rag.service.ReRanker") as mock:
        instance = mock.return_value
        # Mock re-ranking result (returns the first chunk)
        instance.rerank = AsyncMock(side_effect=lambda query_context, chunks, profile: chunks[:5])
        yield instance

@pytest.mark.asyncio
async def test_retrieve_context_success(mock_embedder, mock_vectorstore, mock_reranker):
    """
    Test that RAGService.retrieve_context orchestrates correctly and returns ContextChunks.
    """
    service = RAGService()
    
    skills = ["Python", "Asyncio"]
    role = "Software Engineer"
    
    results = await service.retrieve_context(skills, role)
    
    assert len(results) > 0
    assert isinstance(results[0], ContextChunk)
    assert results[0].text == "This is a test chunk of context about Python fundamentals."
    assert results[0].source == "Python Mastery.pdf"
    assert results[0].score == 0.85
    
    # Verify component calls
    mock_embedder.embed_query.assert_called()
    mock_vectorstore.query.assert_called()
    mock_reranker.rerank.assert_called()

@pytest.mark.asyncio
async def test_retrieve_context_low_score_filtering(mock_embedder, mock_vectorstore, mock_reranker):
    """
    Test that chunks with scores below threshold are filtered out.
    """
    # Set a low score for the mock match
    mock_vectorstore.query.return_value.matches[0].score = 0.5
    
    service = RAGService()
    results = await service.retrieve_context(["Python"], "Software Engineer")
    
    # Should be empty because 0.5 < 0.75 threshold
    assert len(results) == 0

@pytest.mark.asyncio
async def test_retrieve_context_empty_results(mock_embedder, mock_vectorstore, mock_reranker):
    """
    Test behavior when no matches are found in Pinecone.
    """
    mock_vectorstore.query.return_value.matches = []
    
    service = RAGService()
    results = await service.retrieve_context(["Python"], "Software Engineer")
    
    assert results == []
    mock_reranker.rerank.assert_not_called()
