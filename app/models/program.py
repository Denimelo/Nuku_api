from uuid import uuid4
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Date, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class Program(Base):
    __tablename__ = "programs"

    program_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String, nullable=False)  # Nom du programme
    description = Column(String, nullable=True)  # Description du programme
    start_date = Column(Date, nullable=False)  # Date de début
    end_date = Column(Date, nullable=False)  # Date de fin
    max_participants = Column(Integer, nullable=True)  # Nombre maximal de participants
    is_active = Column(Boolean, default=True)  # Programme actif ou non
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)  # Créé par (Admin)
    created_at = Column(DateTime, default=datetime.utcnow)  # Date de création
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # Dernière mise à jour

    created_by_user = relationship("User", back_populates="created_programs", foreign_keys=[created_by])
    experts = relationship("ProgramExpert", back_populates="program")
    participants = relationship("ProgramParticipant", back_populates="program")
    modules = relationship("Module", back_populates="program")
    calls = relationship("Call", back_populates="program")
    messages = relationship("Message", back_populates="program")
    documents = relationship("Document", back_populates="program")

