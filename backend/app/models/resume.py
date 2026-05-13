import uuid
from typing import Optional
from sqlalchemy import String, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class ResumeData(Base):
    __tablename__ = "resume_data"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), index=True, unique=True)
    raw_text: Mapped[str] = mapped_column(Text)
    extracted_skills: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    extracted_techs: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    session: Mapped["Session"] = relationship(back_populates="resume")
