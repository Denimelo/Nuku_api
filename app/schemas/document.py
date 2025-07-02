from pydantic import BaseModel, UUID4
from typing import Optional
from datetime import datetime

class DocumentBase(BaseModel):
    """Schéma de base pour un document."""
    uploaded_by: UUID4
    program_id: Optional[UUID4] = None
    title: str
    description: Optional[str] = None
    file_url: str
    is_public: bool = False

class DocumentCreate(DocumentBase):
    """Schéma pour la création d'un document."""
    pass

class DocumentUpdate(BaseModel):
    """Schéma pour la mise à jour d'un document."""
    title: Optional[str] = None
    description: Optional[str] = None
    file_url: Optional[str] = None
    is_public: Optional[bool] = None

    class Config:
        from_attributes = True

class DocumentResponse(DocumentBase):
    """Schéma de réponse pour un document (lecture seule)."""
    document_id: UUID4
    upload_date: datetime

    class Config:
        from_attributes = True

class DocumentOut(DocumentResponse):
    """Schéma de sortie détaillé pour un document."""
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class DocumentDelete(BaseModel):
    """Schéma pour la suppression d'un document."""
    document_id: UUID4

    class Config:
        from_attributes = True