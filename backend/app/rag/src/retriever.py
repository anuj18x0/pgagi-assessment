from typing import List, Dict, Any, Optional
import json
from google import genai
from app.rag.src.embedder import GoogleEmbedder
from app.rag.src.vectorstore import PineconeStore
import logging

logger = logging.getLogger(__name__)

class QueryConstructor:
    @staticmethod
    def build_queries(skills: List[str], role: str) -> List[str]:
        """
        Build focused queries based on skills and target role.
        """
        queries = []
        # Basic fundamentals query for the role
        queries.append(f"{role} core concepts and fundamental principles")
        
        # Skill-specific queries
        for skill in skills[:3]:  # Top 3 skills
            queries.append(f"{skill} fundamentals and advanced concepts for {role}")
            queries.append(f"applied {skill} techniques and real-world scenarios in {role}")
            
        return list(set(queries))[:5]  # Limit to 5 unique queries

class RAGRetriever:
    def __init__(self, embedder: GoogleEmbedder, vectorstore: PineconeStore):
        self.embedder = embedder
        self.vectorstore = vectorstore
        self.score_threshold = 0.75

    async def retrieve(self, queries: List[str], role_tag: str) -> List[Dict[str, Any]]:
        """
        Perform semantic retrieval with filtering and score thresholding.
        """
        all_results = []
        seen_ids = set()

        for query in queries:
            query_vector = self.embedder.embed_query(query)
            # Filter by role namespace/tag
            filter_dict = {"role_tags": {"$in": [role_tag]}}
            
            results = self.vectorstore.query(
                query_vector=query_vector,
                top_k=8,
                filter=filter_dict
            )

            for match in results.matches:
                if match.score > self.score_threshold and match.id not in seen_ids:
                    all_results.append({
                        "id": match.id,
                        "text": match.metadata["text"],
                        "score": match.score,
                        "metadata": match.metadata
                    })
                    seen_ids.add(match.id)

        # Sort by score and take top 8 across all queries before re-ranking
        all_results.sort(key=lambda x: x["score"], reverse=True)
        return all_results[:8]

class ReRanker:
    def __init__(self, client: genai.Client):
        self.client = client
        self.model_name = "gemini-2.5-flash"

    async def rerank(self, query_context: str, chunks: List[Dict[str, Any]], candidate_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Use Gemini to re-rank chunks by relevance to the candidate profile.
        Keeps top-5.
        """
        if not chunks:
            return []

        chunks_text = "\n\n".join([f"ID: {i}\nText: {c['text']}" for i, c in enumerate(chunks)])
        
        prompt = f"""
        You are an expert technical interviewer. Evaluate the following document chunks for their relevance 
        to assessing a candidate for a {candidate_profile.get('role', 'technical')} role.
        
        Candidate Profile:
        Skills: {', '.join(candidate_profile.get('skills', []))}
        
        Context Chunks:
        {chunks_text}
        
        Task: 
        Select the top 5 chunks that are most relevant for generating technical interview questions 
        that specifically test this candidate's reported skills and their application in the target role.
        
        Return ONLY a JSON list of the original indices (IDs) in order of relevance.
        Example: [3, 0, 1, 4, 2]
        """

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config={
                    "response_mime_type": "application/json"
                }
            )
            
            # Parse the response to get indices
            indices = json.loads(response.text)
            
            # Map back to chunks and keep top 5
            reranked = [chunks[idx] for idx in indices if idx < len(chunks)]
            return reranked[:5]
        except Exception as e:
            logger.error(f"Re-ranking failed: {e}")
            # Fallback to original top-5 if re-ranking fails
            return chunks[:5]
