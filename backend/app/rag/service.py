import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

# Add src to path to allow importing components
src_path = str(Path(__file__).parent / "src")
if src_path not in sys.path:
    sys.path.append(src_path)

from app.rag.src.retriever import QueryConstructor, RAGRetriever, ReRanker
from app.rag.src.embedder import GoogleEmbedder
from app.rag.src.vectorstore import PineconeStore

class ContextChunk(BaseModel):
    text: str
    source: str
    page_range: Optional[str] = None
    score: float

class RAGService:
    def __init__(self):
        # Initialize components
        # These will use environment variables for API keys
        self.embedder = GoogleEmbedder()
        self.vectorstore = PineconeStore(index_name="pgagi-rag")
        self.retriever = RAGRetriever(self.embedder, self.vectorstore)
        self.reranker = ReRanker(self.embedder.client)
        
        # Heuristic mapping for role namespaces
        self.role_map = {
            "Data Scientist": "data_science",
            "ML Engineer": "ai_ml",
            "Software Engineer": "software_eng",
            "Backend Developer": "backend"
        }

    async def retrieve_context(self, skills: List[str], role: str) -> List[ContextChunk]:
        """
        Main entry point for retrieving highly relevant context for a candidate.
        Orchestrates: Query Construction -> Semantic Retrieval -> Gemini Re-ranking.
        """
        # 1. Build focused queries
        queries = QueryConstructor.build_queries(skills, role)
        
        # 2. Determine role tag for filtering
        # Default to a generic tag if exact match not found
        role_tag = self.role_map.get(role, "general")
        
        # 3. Retrieve initial chunks from Pinecone (top 8)
        initial_chunks = await self.retriever.retrieve(queries, role_tag)
        
        if not initial_chunks:
            return []

        # 4. Re-rank with Gemini (top 5)
        candidate_profile = {"skills": skills, "role": role}
        reranked_chunks = await self.reranker.rerank(
            query_context=f"Interviewer seeking context for {role}",
            chunks=initial_chunks,
            candidate_profile=candidate_profile
        )

        # 5. Transform to ContextChunk objects
        return [
            ContextChunk(
                text=chunk["text"],
                source=chunk["metadata"].get("source_book", "Unknown"),
                page_range=chunk["metadata"].get("page_range"),
                score=chunk["score"]
            )
            for chunk in reranked_chunks
        ]
