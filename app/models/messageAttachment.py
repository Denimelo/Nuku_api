from uuid import uuid4
from datetime import datetime
from sqlalchemy import Column, ForeignKey, String, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class MessageAttachment(Base):
    __tablename__ = "message_attachments"

    attachment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.message_id"), nullable=False)
    
    # Métadonnées du fichier
    file_name = Column(String(255), nullable=False)
    original_file_name = Column(String(255), nullable=False)
    file_url = Column(String(500), nullable=False)  # URL Supabase
    file_path = Column(String(500), nullable=False)  # Chemin dans Supabase
    
    # Informations techniques
    file_size = Column(Integer, nullable=False)  # Taille en bytes
    content_type = Column(String(100), nullable=False)  # MIME type
    file_extension = Column(String(10), nullable=True)
    
    # Métadonnées image (si applicable)
    image_width = Column(Integer, nullable=True)
    image_height = Column(Integer, nullable=True)
    
    # Temporalité
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    message = relationship("Message", back_populates="attachments")

    def __repr__(self):
        return f"<MessageAttachment {self.file_name}>"
    
    @property
    def is_image(self) -> bool:
        """Vérifier si c'est une image"""
        image_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        return self.content_type in image_types
    
    @property
    def file_size_mb(self) -> float:
        """Taille du fichier en MB"""
        return round(self.file_size / (1024 * 1024), 2)