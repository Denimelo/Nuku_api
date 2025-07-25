from uuid import uuid4
from datetime import datetime
from sqlalchemy import Column, ForeignKey, String, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class MessageReaction(Base):
    __tablename__ = "message_reactions"

    reaction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.message_id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    
    # Type de réaction
    emoji = Column(String(10), nullable=False)  # 👍, ❤️, 😂, etc.
    reaction_type = Column(String(20), nullable=False)  # like, love, laugh, etc.
    
    # Temporalité
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    message = relationship("Message", back_populates="reactions")
    user = relationship("User")
    
    # Contrainte : un utilisateur ne peut avoir qu'une réaction par message
    __table_args__ = (
        UniqueConstraint('message_id', 'user_id', name='unique_user_message_reaction'),
    )

    def __repr__(self):
        return f"<MessageReaction {self.emoji} by {self.user_id}>"