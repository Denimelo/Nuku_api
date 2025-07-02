from uuid import uuid4
from datetime import datetime
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class Module(Base):
    __tablename__ = "modules"

    module_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    program_id = Column(UUID(as_uuid=True), ForeignKey("programs.program_id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    sequence_number = Column(Integer, nullable=False)  # Ordre d’apparition du module
    created_by = Column(UUID(as_uuid=True), ForeignKey("experts.expert_id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    program = relationship("Program", back_populates="modules")
    contents = relationship("ModuleContent", back_populates="module")
    assignments = relationship("Assignment", back_populates="module")
    created_by_expert = relationship("Expert", back_populates="created_modules", foreign_keys=[created_by])
