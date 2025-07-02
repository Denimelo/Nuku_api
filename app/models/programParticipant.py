import enum
from uuid import uuid4
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class CompletionStatus(str, enum.Enum):
    in_progress = "in_progress"
    completed = "completed"
    dropped = "dropped"

class ProgramParticipant(Base):
    __tablename__ = "program_participants"

    participant_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    program_id = Column(UUID(as_uuid=True), ForeignKey("programs.program_id"), nullable=False)
    entrepreneur_id = Column(UUID(as_uuid=True), ForeignKey("entrepreneurs.entrepreneur_id"), nullable=False)
    enrollment_date = Column(DateTime, default=datetime.utcnow)
    completion_status = Column(Enum(CompletionStatus), default=CompletionStatus.in_progress)
    completion_date = Column(DateTime, nullable=True)

    program = relationship("Program", back_populates="participants")
    entrepreneur = relationship("Entrepreneur", back_populates="program_participations")
