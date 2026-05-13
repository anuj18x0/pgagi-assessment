import uuid
from datetime import datetime
from sqlalchemy import Text, ForeignKey, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    question_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), index=True)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), index=True)
    answer_text: Mapped[str] = mapped_column(Text)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    time_taken_secs: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    question: Mapped["Question"] = relationship(back_populates="answers")
    session: Mapped["Session"] = relationship(back_populates="answers")
