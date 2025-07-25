from uuid import uuid4
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class CallRecording(Base):
    __tablename__ = "call_recordings"

    recording_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    call_id = Column(UUID(as_uuid=True), ForeignKey("calls.call_id"), nullable=False)
    
    # Métadonnées du fichier
    file_name = Column(String(255), nullable=False)
    file_url = Column(String(500), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)  # Taille en bytes
    
    # Métadonnées de l'enregistrement
    duration_seconds = Column(Integer, nullable=False)
    format = Column(String(10), default="mp4")  # mp4, webm, etc.
    quality = Column(String(10), default="720p")  # 720p, 1080p, etc.
    
    # États
    is_processed = Column(Boolean, default=False)
    is_available = Column(Boolean, default=True)
    is_transcribed = Column(Boolean, default=False)
    
    # Transcription (si disponible)
    transcript_url = Column(String(500), nullable=True)
    transcript_language = Column(String(10), default="fr")
    
    # Contrôle d'accès
    is_public = Column(Boolean, default=False)
    password_protected = Column(Boolean, default=False)
    access_password = Column(String(100), nullable=True)
    
    # Temporalité
    recorded_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # Date d'expiration automatique
    
    # Statistiques
    view_count = Column(Integer, default=0)
    download_count = Column(Integer, default=0)
    
    # Relations
    call = relationship("Call")

    def __repr__(self):
        return f"<CallRecording {self.file_name}>"
    
    @property
    def duration_formatted(self) -> str:
        """Durée formatée"""
        hours = self.duration_seconds // 3600
        minutes = (self.duration_seconds % 3600) // 60
        seconds = self.duration_seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    @property
    def file_size_mb(self) -> float:
        """Taille du fichier en MB"""
        return round(self.file_size / (1024 * 1024), 2)