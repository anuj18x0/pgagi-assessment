from uuid import UUID
from typing import List
from sqlalchemy import select
from app.models.question import Question
from app.repositories.base import BaseRepository

class QuestionRepository(BaseRepository[Question]):
    def __init__(self, session):
        super().__init__(Question, session)

    async def get_by_session(self, session_id: UUID) -> List[Question]:
        query = select(self.model).where(self.model.session_id == session_id).order_by(self.model.order_index)
        result = await self.session.execute(query)
        return list(result.scalars().all())
