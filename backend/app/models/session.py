import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, List
from sqlalchemy import String, DateTime, JSON, ForeignKey, Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class SessionStatus(str, Enum):
    CREATED = "created"
    RESUME_UPLOADED = "resume_uploaded"
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    candidate_name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), index=True)
    selected_role: Mapped[str] = mapped_column(String(255))
    status: Mapped[SessionStatus] = mapped_column(
        SqlEnum(SessionStatus), default=SessionStatus.PENDING, index=True
    )
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    questions: Mapped[List["Question"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    answers: Mapped[List["Answer"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    resume: Mapped[Optional["ResumeData"]] = relationship(back_populates="session", uselist=False, cascade="all, delete-orphan")
