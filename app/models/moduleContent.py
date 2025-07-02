from sqlalchemy import Column, String, Enum, DateTime, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4
from app.database import Base
import enum

class ContentType(str, enum.Enum):
    video = "video"
    text = "text"
    pdf = "pdf"
    quiz = "quiz"

class ModuleContent(Base):
    __tablename__ = "module_contents"

    content_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    module_id = Column(UUID(as_uuid=True), ForeignKey("modules.module_id"), nullable=False)
    content_type = Column(Enum(ContentType), nullable=False)
    title = Column(String, nullable=False)
    content_url = Column(String, nullable=True)  # Lien vers fichier ou vidéo
    duration_minutes = Column(Integer, nullable=True)  # Pour les vidéos
    text_content = Column(Text, nullable=True)  # Pour les textes
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    module = relationship("Module", back_populates="contents")
