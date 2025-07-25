from uuid import uuid4
from datetime import datetime
from sqlalchemy import Column, ForeignKey, Text, DateTime, Boolean, String, Integer, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class MessageType(str, enum.Enum):
    direct = "direct"          # Message privé entre 2 utilisateurs
    group = "group"            # Message dans un groupe/programme
    announcement = "announcement"  # Annonce officielle
    system = "system"          # Message système automatique

class MessageStatus(str, enum.Enum):
    sent = "sent"
    delivered = "delivered"
    read = "read"
    failed = "failed"

class MessagePriority(str, enum.Enum):
    low = "low"
    normal = "normal"
    high = "high"
    urgent = "urgent"

class Message(Base):
    __tablename__ = "messages"

    message_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Participants
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    receiver_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)  # Nullable pour messages de groupe
    
    # Contenu
    subject = Column(String(255), nullable=True)  # Sujet du message (optionnel)
    message_text = Column(Text, nullable=False)
    
    # Métadonnées
    message_type = Column(Enum(MessageType), default=MessageType.direct, nullable=False)
    status = Column(Enum(MessageStatus), default=MessageStatus.sent, nullable=False)
    priority = Column(Enum(MessagePriority), default=MessagePriority.normal, nullable=False)
    
    # Contexte (programme, conversation)
    program_id = Column(UUID(as_uuid=True), ForeignKey("programs.program_id"), nullable=True)
    conversation_id = Column(String(255), nullable=True)  # ID de fil de conversation
    parent_message_id = Column(UUID(as_uuid=True), ForeignKey("messages.message_id"), nullable=True)  # Pour les réponses
    
    # Temporalité
    sent_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    delivered_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)  # Pour messages temporaires
    
    # États
    is_read = Column(Boolean, default=False, nullable=False)
    is_deleted_by_sender = Column(Boolean, default=False, nullable=False)
    is_deleted_by_receiver = Column(Boolean, default=False, nullable=False)
    is_starred = Column(Boolean, default=False, nullable=False)  # Message important
    is_archived = Column(Boolean, default=False, nullable=False)
    
    # Métadonnées additionnelles
    edit_count = Column(Integer, default=0)  # Nombre de modifications
    last_edited_at = Column(DateTime, nullable=True)
    ip_address = Column(String(45), nullable=True)  # Pour traçabilité
    user_agent = Column(String(500), nullable=True)  # Navigateur/app utilisée
    
    # Relations
    sender = relationship("User", back_populates="sent_messages", foreign_keys=[sender_id])
    receiver = relationship("User", back_populates="received_messages", foreign_keys=[receiver_id])
    program = relationship("Program", back_populates="messages")
    
    # Auto-référence pour les réponses
    parent_message = relationship("Message", remote_side=[message_id], backref="replies")
    
    # Relation avec les pièces jointes
    attachments = relationship("MessageAttachment", back_populates="message", cascade="all, delete-orphan")
    
    # Relation avec les réactions
    reactions = relationship("MessageReaction", back_populates="message", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Message {self.message_id}: {self.message_text[:50]}...>"
    
    @property
    def is_group_message(self) -> bool:
        """Vérifier si c'est un message de groupe"""
        return self.message_type == MessageType.group or self.program_id is not None
    
    @property
    def conversation_identifier(self) -> str:
        """Identifiant unique de la conversation"""
        if self.conversation_id:
            return self.conversation_id
        elif self.program_id:
            return f"program_{self.program_id}"
        elif self.receiver_id:
            # Créer ID de conversation entre 2 utilisateurs
            user_ids = sorted([str(self.sender_id), str(self.receiver_id)])
            return f"direct_{user_ids[0]}_{user_ids[1]}"
        return f"unknown_{self.message_id}"