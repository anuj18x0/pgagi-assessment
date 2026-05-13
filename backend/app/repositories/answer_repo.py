from uuid import UUID
from typing import List, Optional
from sqlalchemy import select
from app.models.answer import Answer
from app.repositories.base import BaseRepository

class AnswerRepository(BaseRepository[Answer]):
    def __init__(self, session):
        super().__init__(Answer, session)

    async def get_by_session(self, session_id: UUID) -> List[Answer]:
        query = select(self.model).where(self.model.session_id == session_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_question(self, question_id: UUID) -> Optional[Answer]:
        query = select(self.model).where(self.model.question_id == question_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
