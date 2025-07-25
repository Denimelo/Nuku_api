from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timedelta
from uuid import uuid4
from app.database import Base
import enum

class OTPType(str, enum.Enum):
    email_verification = "email_verification"
    password_reset = "password_reset"
    login_verification = "login_verification"

class OTP(Base):
    __tablename__ = "otps"

    otp_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    email = Column(String, nullable=False)
    otp_code = Column(String(6), nullable=False)
    otp_type = Column(String, nullable=False)  # OTPType enum
    is_used = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at