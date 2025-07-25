from uuid import uuid4
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from app.database import Base

class Conversation(Base):
    __tablename__ = "conversations"

    conversation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Identifiant unique de la conversation
    conversation_key = Column(String(255), unique=True, nullable=False)  # Ex: "direct_user1_user2"
    
    # Métadonnées
    title = Column(String(255), nullable=True)  # Titre personnalisé (optionnel)
    description = Column(Text, nullable=True)
    conversation_type = Column(String(20), default="direct")  # direct, group, program
    
    # Participants (stockage JSON des IDs participants)
    participant_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=False)
    participant_count = Column(Integer, default=2)
    
    # États
    is_active = Column(Boolean, default=True)
    is_muted = Column(Boolean, default=False)
    
    # Statistiques
    message_count = Column(Integer, default=0)
    last_message_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Temporalité
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_activity_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Conversation {self.conversation_key}>"
    
    @classmethod
    def generate_direct_key(cls, user1_id: UUID, user2_id: UUID) -> str:
        """Générer clé unique pour conversation directe"""
        user_ids = sorted([str(user1_id), str(user2_id)])
        return f"direct_{user_ids[0]}_{user_ids[1]}"
    
    @classmethod
    def generate_program_key(cls, program_id: UUID) -> str:
        """Générer clé unique pour conversation de programme"""
        return f"program_{program_id}"