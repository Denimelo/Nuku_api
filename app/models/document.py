from sqlalchemy import Column, ForeignKey, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime
from app.database import Base

class Document(Base):
    __tablename__ = "documents"

    document_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    program_id = Column(UUID(as_uuid=True), ForeignKey("programs.program_id"), nullable=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    file_url = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)
    is_public = Column(Boolean, default=True)

    uploaded_by_user = relationship("User", back_populates="uploaded_documents", foreign_keys=[uploaded_by])
    program = relationship("Program", back_populates="documents")
