from uuid import UUID
from typing import List
from app.database import get_db
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from http.client import HTTPException
from app.crud.message import create_message, get_messages, get_message_by_id
from app.schemas.message import MessageCreate, MessageResponse

router = APIRouter(prefix="/messages", tags=["Messages"])
@router.post("/", response_model=MessageResponse)
def create_message_route(data: MessageCreate, db: Session = Depends(get_db)):
    return create_message(db, data)

@router.get("/", response_model=List[MessageResponse])
def list_messages(db: Session = Depends(get_db)):
    return get_messages(db)

@router.get("/{message_id}", response_model=MessageResponse)
def get_message(message_id: UUID, db: Session = Depends(get_db)):
    message = get_message_by_id(db, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return message

@router.put("/{message_id}", response_model=MessageResponse)
def update_message(message_id: UUID, data: MessageCreate, db: Session = Depends(get_db)):
    message = get_message_by_id(db, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return create_message(db, data, message_id)

@router.delete("/{message_id}", response_model=dict)
def delete_message(message_id: UUID, db: Session = Depends(get_db)):
    message = get_message_by_id(db, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    db.delete(message)
    db.commit()
    return {"message": "Message deleted successfully"}

@router.get("/program/{program_id}", response_model=List[MessageResponse])
def get_messages_by_program(program_id: UUID, db: Session = Depends(get_db)):
    messages = db.query(MessageResponse).filter(MessageResponse.program_id == program_id).all()
    if not messages:
        raise HTTPException(status_code=404, detail="No messages found for this program")
    return messages