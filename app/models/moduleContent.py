from uuid import uuid4
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class ContentType(str, enum.Enum):
    text = "text"               # Contenu textuel
    video = "video"             # Vidéo
    audio = "audio"             # Audio/Podcast
    document = "document"       # Document (PDF, DOCX, etc.)
    image = "image"             # Image
    interactive = "interactive" # Contenu interactif
    quiz = "quiz"              # Quiz
    link = "link"              # Lien externe

class ModuleContent(Base):
    __tablename__ = "module_contents"

    content_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    module_id = Column(UUID(as_uuid=True), ForeignKey("modules.module_id"), nullable=False)
    
    # Contenu
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    content_type = Column(Enum(ContentType), nullable=False)
    
    # Contenu selon le type
    text_content = Column(Text, nullable=True)  # Pour type "text"
    file_url = Column(String(500), nullable=True)  # Pour fichiers/vidéos
    file_path = Column(String(500), nullable=True)  # Chemin Supabase
    external_link = Column(String(500), nullable=True)  # Pour liens externes
    
    # Métadonnées fichier
    file_size = Column(Integer, nullable=True)
    file_type = Column(String(50), nullable=True)
    duration_seconds = Column(Integer, nullable=True)  # Pour vidéos/audio
    
    # Organisation
    order_index = Column(Integer, default=0)
    
    # États
    is_visible = Column(Boolean, default=True)
    is_downloadable = Column(Boolean, default=False)
    
    # Temporalité
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    module = relationship("Module", back_populates="contents")
    
    def __repr__(self):
        return f"<ModuleContent {self.title} ({self.content_type})>"
    
    @property
    def is_media(self) -> bool:
        """Vérifier si c'est un contenu média"""
        return self.content_type in [ContentType.video, ContentType.audio]
    
    @property
    def duration_formatted(self) -> str:
        """Durée formatée (HH:MM:SS)"""
        if not self.duration_seconds:
            return "00:00"
        
        hours = self.duration_seconds // 3600
        minutes = (self.duration_seconds % 3600) // 60
        seconds = self.duration_seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"