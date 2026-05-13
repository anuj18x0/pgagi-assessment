from pinecone import Pinecone
from typing import List, Dict, Any
import os
import logging

logger = logging.getLogger(__name__)

class PineconeStore:
    def __init__(self, api_key: str = None, index_name: str = "pgagi-rag"):
        self.api_key = api_key or os.getenv("PINECONE_API_KEY")
        if not self.api_key:
            raise ValueError("Pinecone API Key must be provided or set in PINECONE_API_KEY environment variable")
        
        self.pc = Pinecone(api_key=self.api_key)
        self.index_name = index_name
        self.index = self.pc.Index(self.index_name)

    def upsert_chunks(self, chunks: List[Dict[str, Any]]):
        """
        Upsert chunks to Pinecone.
        Expects chunks to have 'id', 'embedding', and 'metadata'.
        """
        vectors = []
        for chunk in chunks:
            vectors.append({
                "id": chunk["id"],
                "values": chunk["embedding"],
                "metadata": chunk["metadata"]
            })

        # Pinecone upsert limit is usually 100-1000 per call depending on vector size
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i : i + batch_size]
            try:
                self.index.upsert(vectors=batch)
                logger.info(f"Upserted batch {i//batch_size} ({len(batch)} vectors)")
            except Exception as e:
                logger.error(f"Error upserting batch {i//batch_size}: {e}")
                raise

    def query(self, query_vector: List[float], top_k: int = 5, filter: Dict[str, Any] = None):
        """
        Query Pinecone for similar vectors.
        """
        return self.index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True,
            filter=filter
        )
