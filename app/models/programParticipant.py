import enum
from uuid import uuid4
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class CompletionStatus(str, enum.Enum):
    in_progress = "in_progress"
    completed = "completed"
    dropped = "dropped"

class EnrollmentStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved" 
    rejected = "rejected"

class ProgramParticipant(Base):
    __tablename__ = "program_participants"

    participant_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    program_id = Column(UUID(as_uuid=True), ForeignKey("programs.program_id"), nullable=False)
    entrepreneur_id = Column(UUID(as_uuid=True), ForeignKey("entrepreneurs.entrepreneur_id"), nullable=False)
    
    # Dates
    enrollment_request_date = Column(DateTime, default=datetime.utcnow)  # Date de la demande
    enrollment_approved_date = Column(DateTime, nullable=True)  # Date d'approbation
    completion_date = Column(DateTime, nullable=True)
    
    # Statuts
    enrollment_status = Column(Enum(EnrollmentStatus), default=EnrollmentStatus.pending)
    completion_status = Column(Enum(CompletionStatus), default=CompletionStatus.in_progress)
    
    # Validation
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    rejection_reason = Column(String, nullable=True)

    # Relations
    program = relationship("Program", back_populates="participants")
    entrepreneur = relationship("Entrepreneur", back_populates="program_participations")
    approved_by_user = relationship("User", foreign_keys=[approved_by])