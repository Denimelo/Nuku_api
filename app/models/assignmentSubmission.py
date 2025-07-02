from uuid import uuid4
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class AssignmentSubmission(Base):
    __tablename__ = "assignment_submissions"

    submission_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    assignment_id = Column(UUID(as_uuid=True), ForeignKey("assignments.assignment_id"), nullable=False)
    entrepreneur_id = Column(UUID(as_uuid=True), ForeignKey("entrepreneurs.entrepreneur_id"), nullable=False)
    submission_text = Column(Text, nullable=True)
    submission_url = Column(String, nullable=True)  # Fichier joint
    submission_date = Column(DateTime, default=datetime.utcnow)
    grade = Column(Integer, nullable=True)
    feedback = Column(Text, nullable=True)
    graded_by = Column(UUID(as_uuid=True), ForeignKey("experts.expert_id"), nullable=True)  # Expert correcteur
    graded_at = Column(DateTime, nullable=True)

    assignment = relationship("Assignment", back_populates="submissions")
    entrepreneur = relationship("Entrepreneur", back_populates="assignment_submissions")
    graded_by_expert = relationship("Expert", back_populates="graded_submissions", foreign_keys=[graded_by])
