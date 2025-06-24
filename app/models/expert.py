from sqlalchemy import Column, String, Integer, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from uuid import uuid4
from app.database import Base


class Expert(Base):
    __tablename__ = "experts"

    expert_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, unique=True)
    specialization = Column(String, nullable=False)
    years_of_experience = Column(Integer, nullable=True)
    linkedin_profile = Column(String, nullable=True)
    cv_url = Column(String, nullable=True)
    bio = Column(String, nullable=True)
    hourly_rate = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="expert_profile", foreign_keys=[user_id])