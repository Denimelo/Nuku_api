from sqlalchemy import Column, String, DateTime, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4
from app.database import Base
import enum
class UserType(str, enum.Enum):
    entrepreneur = "entrepreneur"
    expert = "expert"
    admin = "admin"
class UserStatus(str, enum.Enum):
    pending = "pending"
    active = "active"
    suspended = "suspended"
class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    city = Column(String, nullable=True)
    country = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)
    user_type = Column(Enum(UserType), nullable=False)
    status = Column(Enum(UserStatus), default=UserStatus.pending)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    temporary_password_expiration = Column(DateTime, nullable=True)
    is_temporary_password = Column(Boolean, default=False)

    # Relations with other models

    entrepreneur_profile = relationship("Entrepreneur",back_populates="user",uselist=False,foreign_keys="Entrepreneur.user_id")
    expert_profile = relationship("Expert",back_populates="user",uselist=False,foreign_keys="Expert.user_id")
    created_programs = relationship("Program", back_populates="created_by_user")
    assigned_expert_roles = relationship("ProgramExpert", back_populates="assigned_by_user")
    sent_messages = relationship("Message", back_populates="sender", foreign_keys='Message.sender_id')
    received_messages = relationship("Message", back_populates="receiver", foreign_keys='Message.receiver_id')
    message_reactions = relationship("MessageReaction", back_populates="user")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    notification_preferences = relationship("UserNotificationPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan")  
    call_participations = relationship("CallParticipant", back_populates="user", foreign_keys="CallParticipant.user_id")
