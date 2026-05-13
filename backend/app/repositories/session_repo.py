from uuid import UUID
from typing import Optional
from sqlalchemy import select
from app.models.session import Session, SessionStatus
from app.repositories.base import BaseRepository

class SessionRepository(BaseRepository[Session]):
    def __init__(self, session):
        super().__init__(Session, session)

    async def get_by_email(self, email: str) -> Optional[Session]:
        query = select(self.model).where(self.model.email == email)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_status(self, id: UUID, status: SessionStatus) -> Optional[Session]:
        return await self.update(id, status=status)
