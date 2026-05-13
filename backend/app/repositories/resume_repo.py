from uuid import UUID
from typing import Optional
from sqlalchemy import select
from app.models.resume import ResumeData
from app.repositories.base import BaseRepository

class ResumeRepository(BaseRepository[ResumeData]):
    def __init__(self, session):
        super().__init__(ResumeData, session)

    async def get_by_session(self, session_id: UUID) -> Optional[ResumeData]:
        query = select(self.model).where(self.model.session_id == session_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
