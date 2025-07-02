from uuid import uuid4
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class Assignment(Base):
    __tablename__ = "assignments"

    assignment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    module_id = Column(UUID(as_uuid=True), ForeignKey("modules.module_id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=False)
    max_points = Column(Integer, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("experts.expert_id"), nullable=False)  # Expert
    created_at = Column(DateTime, default=datetime.utcnow)

    module = relationship("Module", back_populates="assignments")
    submissions = relationship("AssignmentSubmission", back_populates="assignment")
    created_by_expert = relationship("Expert", back_populates="created_assignments", foreign_keys=[created_by])
