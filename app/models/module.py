from uuid import uuid4
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey, DateTime, Float, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class ModuleType(str, enum.Enum):
    lesson = "lesson"           # Leçon théorique
    workshop = "workshop"       # Atelier pratique
    assessment = "assessment"   # Évaluation
    project = "project"         # Projet
    discussion = "discussion"   # Discussion/Forum

class ModuleDifficulty(str, enum.Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"
    expert = "expert"

class ModuleStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    archived = "archived"

class Module(Base):
    __tablename__ = "modules"

    module_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Contenu principal
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    learning_objectives = Column(Text, nullable=True)  # Objectifs d'apprentissage
    
    # Métadonnées pédagogiques
    module_type = Column(Enum(ModuleType), default=ModuleType.lesson)
    difficulty_level = Column(Enum(ModuleDifficulty), default=ModuleDifficulty.beginner)
    estimated_duration_minutes = Column(Integer, nullable=True)  # Durée estimée
    
    # Organisation
    program_id = Column(UUID(as_uuid=True), ForeignKey("programs.program_id"), nullable=False)
    order_index = Column(Integer, default=0)  # Ordre dans le programme
    
    # États
    status = Column(Enum(ModuleStatus), default=ModuleStatus.draft)
    is_mandatory = Column(Boolean, default=True)
    is_visible = Column(Boolean, default=True)
    
    # Prérequis et conditions
    prerequisite_modules = Column(String(500), nullable=True)  # JSON des IDs modules prérequis
    minimum_score_required = Column(Float, nullable=True)  # Score minimum pour valider
    
    # Métadonnées
    created_by = Column(UUID(as_uuid=True), ForeignKey("experts.expert_id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)
    
    # Statistiques
    view_count = Column(Integer, default=0)
    completion_count = Column(Integer, default=0)
    average_rating = Column(Float, default=0.0)
    
    # Relations
    program = relationship("Program", back_populates="modules")
    created_by_expert = relationship("Expert", back_populates="created_modules", foreign_keys=[created_by])
    contents = relationship("ModuleContent", back_populates="module", cascade="all, delete-orphan")
    assignments = relationship("Assignment", back_populates="module", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Module {self.title}>"
    
    @property
    def total_content_count(self) -> int:
        """Nombre total de contenus"""
        return len(self.contents)
    
    @property
    def is_published(self) -> bool:
        """Vérifier si le module est publié"""
        return self.status == ModuleStatus.published