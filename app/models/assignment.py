from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey, DateTime, Float, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class AssignmentType(str, enum.Enum):
    quiz = "quiz"
    essay = "essay"
    project = "project"
    presentation = "presentation"
    practical = "practical"
    peer_review = "peer_review"

class AssignmentStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    closed = "closed"

class Assignment(Base):
    __tablename__ = "assignments"

    assignment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Contenu
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    instructions = Column(Text, nullable=True)
    
    # Type et configuration
    assignment_type = Column(Enum(AssignmentType), nullable=False)
    max_score = Column(Float, default=100.0)
    passing_score = Column(Float, default=60.0)
    
    # Temporalité
    due_date = Column(DateTime, nullable=True)
    available_from = Column(DateTime, nullable=True)
    available_until = Column(DateTime, nullable=True)
    
    # Restrictions
    max_attempts = Column(Integer, default=1)
    time_limit_minutes = Column(Integer, nullable=True)
    
    # États
    status = Column(Enum(AssignmentStatus), default=AssignmentStatus.draft)
    is_graded = Column(Boolean, default=True)
    allow_late_submission = Column(Boolean, default=False)
    
    # Relations
    module_id = Column(UUID(as_uuid=True), ForeignKey("modules.module_id"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("experts.expert_id"), nullable=False)
    
    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Statistiques
    submission_count = Column(Integer, default=0)
    average_score = Column(Float, default=0.0)
    
    # Relations
    module = relationship("Module", back_populates="assignments")
    created_by_expert = relationship("Expert", back_populates="created_assignments", foreign_keys=[created_by])
    submissions = relationship("AssignmentSubmission", back_populates="assignment", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Assignment {self.title}>"
    
    @property
    def is_available(self) -> bool:
        """Vérifier si l'assignment est disponible"""
        now = datetime.utcnow()
        
        if self.available_from and now < self.available_from:
            return False
        
        if self.available_until and now > self.available_until:
            return False
        
        return self.status == AssignmentStatus.published
    
    @property
    def is_overdue(self) -> bool:
        """Vérifier si l'assignment est en retard"""
        if not self.due_date:
            return False
        return datetime.utcnow() > self.due_date
    
    @property
    def time_remaining(self) -> timedelta:
        """Temps restant avant échéance"""
        if not self.due_date:
            return timedelta(days=365)  # Pas de limite
        return self.due_date - datetime.utcnow()