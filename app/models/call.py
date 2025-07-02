
from uuid import uuid4
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class Call(Base):
    __tablename__ = "calls"

    call_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    program_id = Column(UUID(as_uuid=True), ForeignKey("programs.program_id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    scheduled_time = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, nullable=True)
    expert_id = Column(UUID(as_uuid=True), ForeignKey("experts.expert_id"), nullable=False)
    max_participants = Column(Integer, nullable=True)
    meeting_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    program = relationship("Program", back_populates="calls")
    expert = relationship("Expert", back_populates="calls_hosted")
    participants = relationship("CallParticipant", back_populates="call")
