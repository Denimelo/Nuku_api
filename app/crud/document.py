from sqlalchemy.orm import Session
from uuid import UUID
from app.models.document import Document
from app.schemas.document import DocumentCreate, DocumentUpdate

def create_document(db: Session, document_in: DocumentCreate):
    document = Document(**document_in.dict())
    db.add(document)
    db.commit()
    db.refresh(document)
    return document

def get_document(db: Session, document_id: UUID):
    return db.query(Document).filter(Document.document_id == document_id).first()

def get_documents(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Document).offset(skip).limit(limit).all()

def update_document(db: Session, document_id: UUID, document_in: DocumentUpdate):
    document = db.query(Document).filter(Document.document_id == document_id).first()
    if not document:
        return None
    for field, value in document_in.dict(exclude_unset=True).items():
        setattr(document, field, value)
    db.commit()
    db.refresh(document)
    return document

def delete_document(db: Session, document_id: UUID):
    document = db.query(Document).filter(Document.document_id == document_id).first()
    if not document:
        return None
    db.delete(document)
    db.commit()
    return document

def get_document_by_id(db: Session, document_id: UUID):
    return db.query(Document).filter(Document.document_id == document_id).first()

def get_documents_by_program_id(db: Session, program_id: UUID):
    return db.query(Document).filter(Document.program_id == program_id).all()

def get_documents_by_user_id(db: Session, user_id: UUID):
    return db.query(Document).filter(Document.user_id == user_id).all()

def get_documents_by_module_id(db: Session, module_id: UUID):
    return db.query(Document).filter(Document.module_id == module_id).all()

def get_documents_by_call_id(db: Session, call_id: UUID):
    return db.query(Document).filter(Document.call_id == call_id).all()