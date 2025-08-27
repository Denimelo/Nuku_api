from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
from app.utils.uuid import uuid_column
from datetime import datetime
import enum

class MentoringStatus(enum.Enum):
    active = "active"
    completed = "completed" 
    inactive = "inactive"

class ExpertMentoring(Base):
    __tablename__ = "expert_mentoring"
    
    mentoring_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_column)
    expert_id = Column(UUID(as_uuid=True), ForeignKey("experts.expert_id"), nullable=False)
    entrepreneur_id = Column(UUID(as_uuid=True), ForeignKey("entrepreneurs.entrepreneur_id"), nullable=False)
    
    assigned_date = Column(DateTime, default=datetime.utcnow)
    completed_date = Column(DateTime, nullable=True)
    status = Column(String, default=MentoringStatus.active.value)
    completion_reason = Column(String, nullable=True)
    
    # Relations
    expert = relationship("Expert", back_populates="mentorings")
    entrepreneur = relationship("Entrepreneur", back_populates="mentorings")