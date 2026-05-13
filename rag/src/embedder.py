from google import genai
from typing import List, Dict, Any
import os
import logging

logger = logging.getLogger(__name__)

class GoogleEmbedder:
    def __init__(self, api_key: str = None, model_name: str = "text-embedding-004"):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Google API Key must be provided or set in GOOGLE_API_KEY environment variable")
        
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = model_name
        self.batch_size = 100
        self.dimension = 768

    async def embed_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Embed a list of chunks in batches.
        Adds 'embedding' key to each chunk dictionary.
        """
        texts = [chunk["text"] for chunk in chunks]
        all_embeddings = []

        for i in range(0, len(texts), self.batch_size):
            batch_texts = texts[i : i + self.batch_size]
            try:
                # Batch embed call using new SDK
                result = self.client.models.embed_content(
                    model=self.model_name,
                    contents=batch_texts,
                    config={
                        "task_type": "RETRIEVAL_DOCUMENT"
                    }
                )
                all_embeddings.extend([e.values for e in result.embeddings])
            except Exception as e:
                logger.error(f"Error embedding batch {i//self.batch_size}: {e}")
                raise

        # Map embeddings back to chunks
        for chunk, embedding in zip(chunks, all_embeddings):
            chunk["embedding"] = embedding
            
        return chunks

    def embed_query(self, query: str) -> List[float]:
        """
        Embed a single query for retrieval.
        """
        result = self.client.models.embed_content(
            model=self.model_name,
            contents=query,
            config={
                "task_type": "RETRIEVAL_QUERY"
            }
        )
        return result.embeddings[0].values
