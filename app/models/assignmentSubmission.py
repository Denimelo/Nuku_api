from uuid import uuid4
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey, DateTime, Float, Enum
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class SubmissionStatus(str, enum.Enum):
    draft = "draft"
    submitted = "submitted"
    graded = "graded"
    returned = "returned"

class AssignmentSubmission(Base):
    __tablename__ = "assignment_submissions"

    submission_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Relations
    assignment_id = Column(UUID(as_uuid=True), ForeignKey("assignments.assignment_id"), nullable=False)
    entrepreneur_id = Column(UUID(as_uuid=True), ForeignKey("entrepreneurs.entrepreneur_id"), nullable=False)
    
    # Contenu de la soumission
    submission_text = Column(Text, nullable=True)
    submission_files = Column(JSON, nullable=True)  # URLs des fichiers soumis
    
    # États
    status = Column(Enum(SubmissionStatus), default=SubmissionStatus.draft)
    attempt_number = Column(Integer, default=1)
    
    # Évaluation
    score = Column(Float, nullable=True)
    grade = Column(String(10), nullable=True)  # A, B, C, D, F ou Excellent, Bien, etc.
    feedback = Column(Text, nullable=True)
    graded_by = Column(UUID(as_uuid=True), ForeignKey("experts.expert_id"), nullable=True)
    
    # Temporalité
    submitted_at = Column(DateTime, nullable=True)
    graded_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Métadonnées
    time_spent_minutes = Column(Integer, nullable=True)
    ip_address = Column(String(45), nullable=True)
    
    # Relations
    assignment = relationship("Assignment", back_populates="submissions")
    entrepreneur = relationship("Entrepreneur", back_populates="assignment_submissions")
    graded_by_expert = relationship("Expert", back_populates="graded_submissions", foreign_keys=[graded_by])
    
    def __repr__(self):
        return f"<AssignmentSubmission {self.submission_id}>"
    
    @property
    def is_late(self) -> bool:
        """Vérifier si la soumission est en retard"""
        if not self.assignment.due_date or not self.submitted_at:
            return False
        return self.submitted_at > self.assignment.due_date
    
    @property
    def is_passing(self) -> bool:
        """Vérifier si la note est suffisante"""
        if not self.score:
            return False
        return self.score >= self.assignment.passing_score
    
    @property
    def grade_percentage(self) -> float:
        """Note en pourcentage"""
        if not self.score or not self.assignment.max_score:
            return 0.0
        return (self.score / self.assignment.max_score) * 100