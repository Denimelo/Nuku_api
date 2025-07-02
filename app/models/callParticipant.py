from uuid import uuid4
import enum
from datetime import datetime
from sqlalchemy import Column, ForeignKey, Integer, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class AttendanceStatus(str, enum.Enum):
    registered = "registered"
    attended = "attended"
    no_show = "no_show"

class CallParticipant(Base):
    __tablename__ = "call_participants"

    call_participant_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    call_id = Column(UUID(as_uuid=True), ForeignKey("calls.call_id"), nullable=False)
    entrepreneur_id = Column(UUID(as_uuid=True), ForeignKey("entrepreneurs.entrepreneur_id"), nullable=False)
    attendance_status = Column(Enum(AttendanceStatus), default=AttendanceStatus.registered)
    feedback_rating = Column(Integer, nullable=True)  # Note 1 à 5
    feedback_comment = Column(Text, nullable=True)

    call = relationship("Call", back_populates="participants")
    entrepreneur = relationship("Entrepreneur", back_populates="call_participations")
