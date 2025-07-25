from datetime import datetime
from enum import Enum as PyEnum
import uuid
from sqlalchemy import Boolean, Column, DateTime, String, Enum
from sqlalchemy.dialects.postgresql import UUID as SQLUUID  # important

from app.database import Base

class TypeNotification(str, PyEnum):
    info = "info"
    warning = "warning"
    error = "error"
    success = "success"

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(SQLUUID(as_uuid=True), nullable=False)
    user_type = Column(String, nullable=False)
    titre = Column(String, nullable=False)
    message = Column(String, nullable=False)
    type = Column(Enum(TypeNotification), default=TypeNotification.info)
    lu = Column(Boolean, default=False)
    date_envoi = Column(DateTime, default=datetime.utcnow)