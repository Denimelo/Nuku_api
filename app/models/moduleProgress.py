from uuid import uuid4
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class ModuleProgress(Base):
    __tablename__ = "module_progress"

    progress_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Relations
    module_id = Column(UUID(as_uuid=True), ForeignKey("modules.module_id"), nullable=False)
    entrepreneur_id = Column(UUID(as_uuid=True), ForeignKey("entrepreneurs.entrepreneur_id"), nullable=False)
    
    # Progression
    completion_percentage = Column(Float, default=0.0)
    contents_completed = Column(Integer, default=0)
    total_contents = Column(Integer, default=0)
    
    # États
    is_started = Column(Boolean, default=False)
    is_completed = Column(Boolean, default=False)
    
    # Temporalité
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    last_accessed_at = Column(DateTime, default=datetime.utcnow)
    
    # Métadonnées
    time_spent_minutes = Column(Integer, default=0)
    last_content_id = Column(UUID(as_uuid=True), nullable=True)  # Dernier contenu consulté
    
    # Relations
    module = relationship("Module")
    entrepreneur = relationship("Entrepreneur")
    
    def __repr__(self):
        return f"<ModuleProgress {self.completion_percentage}%>"
    
    @property
    def progress_status(self) -> str:
        """Statut de progression"""
        if not self.is_started:
            return "Non commencé"
        elif self.is_completed:
            return "Terminé"
        elif self.completion_percentage >= 50:
            return "En cours avancé"
        else:
            return "En cours"