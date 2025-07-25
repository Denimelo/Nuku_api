from uuid import UUID
from typing import List
from app.database import get_db
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from http.client import HTTPException
from app.crud.callParticipant import (create_call_participant,get_call_participants,get_call_participant_by_id,update_call_participant,delete_call_participant,)
from app.schemas.callParticipant import CallParticipantCreate, CallParticipantResponse

router = APIRouter(prefix="/call_participant", tags=["Call Participant"])

@router.post("/", response_model=CallParticipantResponse)
def create_call_participant_route(data: CallParticipantCreate, db: Session = Depends(get_db)):
    return create_call_participant(db, data)

@router.get("/", response_model=List[CallParticipantResponse])
def list_call_participants(db: Session = Depends(get_db)):
    return get_call_participants(db)

@router.get("/{call_participant_id}", response_model=CallParticipantResponse)
def get_call_participant(call_participant_id: UUID, db: Session = Depends(get_db)):
    call_participant = get_call_participant_by_id(db, call_participant_id)
    if not call_participant:
        raise HTTPException(status_code=404, detail="Call Participant not found")
    return call_participant

@router.put("/{call_participant_id}", response_model=CallParticipantResponse)
def update_call_participant(call_participant_id: UUID, data: CallParticipantCreate, db: Session = Depends(get_db)):
    call_participant = get_call_participant_by_id(db, call_participant_id)
    if not call_participant:
        raise HTTPException(status_code=404, detail="Call Participant not found")
    return update_call_participant(db, data, call_participant_id)

