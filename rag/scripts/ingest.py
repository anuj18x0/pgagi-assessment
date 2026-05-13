import os
import sys
import asyncio
import hashlib
import json
from pathlib import Path
from typing import List, Dict, Any

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from loader import PDFLoader
from chunker import RecursiveChunker
from embedder import GoogleEmbedder
from vectorstore import PineconeStore

def generate_id(text: str, metadata: Dict[str, Any]) -> str:
    """
    Generate a stable, unique hash for a chunk based on its content and source.
    Ensures idempotency during upserts.
    """
    payload = {
        "text": text,
        "source": metadata.get("source_book", ""),
        "index": metadata.get("chunk_index", 0)
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()

async def ingest_book(
    file_path: str, 
    metadata_defaults: Dict[str, Any],
    loader: PDFLoader,
    chunker: RecursiveChunker,
    embedder: GoogleEmbedder,
    vectorstore: PineconeStore
):
    print(f"Processing: {file_path}")
    
    # 1. Load PDF
    with open(file_path, "rb") as f:
        pdf_bytes = f.read()
    
    text = loader.extract_text(pdf_bytes)
    
    # 2. Chunk
    chunks = chunker.split_text(text, metadata_defaults)
    print(f"Generated {len(chunks)} chunks")
    
    # 3. Add stable IDs for idempotency
    for chunk in chunks:
        chunk["id"] = generate_id(chunk["text"], chunk["metadata"])
    
    # 4. Embed
    print("Embedding chunks...")
    chunks = await embedder.embed_chunks(chunks)
    
    # 5. Upsert to Pinecone
    print("Upserting to Pinecone...")
    vectorstore.upsert_chunks(chunks)
    print(f"Finished ingesting {file_path}")

async def main():
    # Configuration (In production these would come from env or CLI args)
    loader = PDFLoader()
    chunker = RecursiveChunker(chunk_size=512, chunk_overlap=64)
    embedder = GoogleEmbedder()
    vectorstore = PineconeStore(index_name="pgagi-rag")
    
    books_dir = Path(__file__).parent.parent / "books"
    
    # Example ingestion (can be expanded to iterate over the books directory)
    # We can use role_tags as defined in the request
    for pdf_file in books_dir.glob("*.pdf"):
        metadata = {
            "source_book": pdf_file.name,
            "role_tags": ["ai_ml", "data_science"], # Placeholder tags
            "chapter_title": "General", # Heuristic/Metadata extraction needed for real chapters
            "page_range": "unknown"
        }
        await ingest_book(pdf_file, metadata, loader, chunker, embedder, vectorstore)

if __name__ == "__main__":
    asyncio.run(main())
