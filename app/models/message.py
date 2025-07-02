from uuid import uuid4
from datetime import datetime
from sqlalchemy import Column, ForeignKey, Text, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class Message(Base):
    __tablename__ = "messages"

    message_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    receiver_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    program_id = Column(UUID(as_uuid=True), ForeignKey("programs.program_id"), nullable=True)
    message_text = Column(Text, nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    read_status = Column(Boolean, default=False)

    sender = relationship("User", back_populates="sent_messages", foreign_keys=[sender_id])
    receiver = relationship("User", back_populates="received_messages", foreign_keys=[receiver_id])
    program = relationship("Program", back_populates="messages")
