from uuid import uuid4
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.call import CallType, CallPriority

class CallTemplate(Base):
    __tablename__ = "call_templates"

    template_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Métadonnées
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)  # "mentorat", "formation", "evaluation"
    
    # Configuration par défaut
    call_type = Column(Enum(CallType), nullable=False)
    priority = Column(Enum(CallPriority), default=CallPriority.normal)
    default_duration_minutes = Column(Integer, default=60)
    
    # Contenu pré-défini
    default_agenda = Column(Text, nullable=True)
    preparation_checklist = Column(JSON, nullable=True)  # Liste de préparation
    default_questions = Column(JSON, nullable=True)  # Questions types
    
    # Configuration technique
    platform = Column(String(50), default="zoom")
    requires_approval = Column(Boolean, default=False)
    max_participants = Column(Integer, nullable=True)
    is_recorded = Column(Boolean, default=False)
    
    # Métadonnées
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Usage
    is_active = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)
    
    # Relations
    created_by_user = relationship("User")

    def __repr__(self):
        return f"<CallTemplate {self.name}>"