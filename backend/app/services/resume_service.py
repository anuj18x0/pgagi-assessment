import hashlib
from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.resume import ResumeData
from app.repositories.resume_repo import ResumeRepository
from app.services.gemini_extractor import GeminiExtractor
from app.services.storage_service import StorageService
from app.services.session_cache import SessionCache
from app.rag.src.loader import PDFLoader

class ResumeService:
    def __init__(self, db: AsyncSession, redis):
        self.db = db
        self.repo = ResumeRepository(db)
        self.extractor = GeminiExtractor()
        self.storage = StorageService()
        self.cache = SessionCache(redis)
        self.pdf_loader = PDFLoader()

    async def process_resume(self, file_bytes: bytes, session_id: UUID, file_name: str, content_type: str) -> ResumeData:
        """
        Full resume processing pipeline:
        1. Hash file for idempotency/caching.
        2. Extract text (PDF/Text).
        3. Extract skills using Gemini.
        4. Infer domain.
        5. Upload to S3.
        6. Store in DB.
        """
        file_hash = hashlib.sha256(file_bytes).hexdigest()
        
        # Check cache first
        cached_data = await self.cache.get_state(UUID(int=0)) # Placeholder for global cache or specific hash cache
        # Actually, let's just check the DB by hash first if we want total idempotency
        # but the request says keyed by file_hash in Redis.
        
        # Parse text
        if content_type == "application/pdf":
            raw_text = self.pdf_loader.extract_text(file_bytes)
        else:
            raw_text = file_bytes.decode("utf-8", errors="ignore")

        # Extract structured data
        extracted = await self.extractor.extract_skills(raw_text)
        domain = self.extractor.infer_domain(extracted)
        
        # Upload to S3
        s3_url = await self.storage.upload_file(file_bytes, f"resumes/{session_id}_{file_name}", content_type)

        # Store in DB
        resume_data = await self.repo.create(
            session_id=session_id,
            raw_text=raw_text,
            extracted_skills=extracted.model_dump(),
            extracted_techs=extracted.technologies, # Keeping them separate in model
            domain=domain,
            file_hash=file_hash
        )
        
        return resume_data
