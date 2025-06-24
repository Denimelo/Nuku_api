from sqlalchemy import Column, String, Date, Integer, Boolean, Enum, ForeignKey, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4
from app.database import Base
import enum


class ValidationStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class Entrepreneur(Base):
    __tablename__ = "entrepreneurs"

    entrepreneur_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, unique=True)
    company_name = Column(String, nullable=False)
    company_registration_number = Column(String, nullable=True)
    company_description = Column(String, nullable=True)
    industry_sector = Column(String, nullable=True)
    founding_date = Column(Date, nullable=True)
    number_of_employees = Column(Integer, nullable=True)
    annual_revenue = Column(Float, nullable=True)
    has_raised_funds = Column(Boolean, default=False)
    amount_raised = Column(Float, nullable=True)
    wants_to_raise_funds = Column(Boolean, default=False)
    desired_funding_amount = Column(Float, nullable=True)
    validation_status = Column(Enum(ValidationStatus), default=ValidationStatus.pending)
    validation_date = Column(DateTime, nullable=True)
    validated_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)

# ✅ RELATION CORRIGÉE
    user = relationship("User", back_populates="entrepreneur_profile", foreign_keys=[user_id])