from uuid import UUID
from typing import List
from app.database import get_db
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from http.client import HTTPException
from app.crud.document import (
    create_document,
    get_documents,
    get_document_by_id,
    update_document,
    delete_document,
)
from app.schemas.document import DocumentCreate, DocumentResponse

router = APIRouter(prefix="/documents", tags=["Documents"]) 
@router.post("/", response_model=DocumentResponse)
def create_document_route(data: DocumentCreate, db: Session = Depends(get_db)):
    return create_document(db, data)

@router.get("/", response_model=List[DocumentResponse])
def list_documents(db: Session = Depends(get_db)):
    return get_documents(db)

@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: UUID, db: Session = Depends(get_db)): 
    document = get_document_by_id(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document

@router.put("/{document_id}", response_model=DocumentResponse)
def update_document_route(document_id: UUID, data: DocumentCreate, db: Session = Depends(get_db)):
    document = get_document_by_id(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return update_document(db, data, document_id)

@router.delete("/{document_id}", response_model=dict)
def delete_document_route(document_id: UUID, db: Session = Depends(get_db)):
    document = get_document_by_id(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    delete_document(db, document_id)
    return {"message": "Document deleted successfully"}

@router.get("/program/{program_id}", response_model=List[DocumentResponse])
def get_documents_by_program(program_id: UUID, db: Session = Depends(get_db)):
    documents = db.query(DocumentResponse).filter(DocumentResponse.program_id == program_id).all()
    if not documents:
        raise HTTPException(status_code=404, detail="No documents found for this program")
    return documents