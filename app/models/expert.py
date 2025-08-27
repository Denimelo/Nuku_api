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

    # 🔁 Relation avec les programmes auxquels l'expert est assigné
    __table_args__ = (
        {"comment": "Table des experts, qui sont des utilisateurs avec des compétences spécifiques pour mentorat ou enseignement."}
    )
    user = relationship("User", back_populates="expert_profile", foreign_keys=[user_id])
    created_modules = relationship("Module", back_populates="created_by_expert")
    created_assignments = relationship("Assignment", back_populates="created_by_expert")
    graded_submissions = relationship("AssignmentSubmission", back_populates="graded_by_expert")
    calls_hosted = relationship("Call", back_populates="expert")
    program_assignments = relationship("ProgramExpert", back_populates="expert")
    mentorings = relationship("ExpertMentoring", back_populates="expert")
