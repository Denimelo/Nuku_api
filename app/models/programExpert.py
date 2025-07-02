from uuid import uuid4
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class ProgramExpert(Base):
    __tablename__ = "program_experts"

    program_expert_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    program_id = Column(UUID(as_uuid=True), ForeignKey("programs.program_id"), nullable=False)
    expert_id = Column(UUID(as_uuid=True), ForeignKey("experts.expert_id"), nullable=False)
    role = Column(String, nullable=False)  # Rôle de l'expert (mentor, instructeur, etc.)
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    assigned_at = Column(DateTime, default=datetime.utcnow)

    program = relationship("Program", back_populates="experts")
    expert = relationship("Expert", back_populates="program_assignments")
    assigned_by_user = relationship("User", back_populates="assigned_expert_roles", foreign_keys=[assigned_by])
