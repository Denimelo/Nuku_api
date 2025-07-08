from sqlalchemy.orm import Session
from uuid import UUID

from app.models.callParticipant import CallParticipant
from app.schemas.callParticipant import CallParticipantCreate, CallParticipantUpdate

def create_call_participant(db: Session, call_participant_in: CallParticipantCreate):
    call_participant = CallParticipant(**call_participant_in.dict())
    db.add(call_participant)
    db.commit()
    db.refresh(call_participant)
    return call_participant

def get_call_participant(db: Session, call_participant_id: UUID):
    return db.query(CallParticipant).filter(CallParticipant.call_participant_id == call_participant_id).first()

def get_call_participants(db: Session, skip: int = 0, limit: int = 100):
    return db.query(CallParticipant).offset(skip).limit(limit).all()

def update_call_participant(db: Session, call_participant_id: UUID, call_participant_in: CallParticipantUpdate):
    call_participant = db.query(CallParticipant).filter(CallParticipant.call_participant_id == call_participant_id).first()
    if not call_participant:
        return None
    for field, value in call_participant_in.dict(exclude_unset=True).items():
        setattr(call_participant, field, value)
    db.commit()
    db.refresh(call_participant)
    return call_participant

def delete_call_participant(db: Session, call_participant_id: UUID):
    call_participant = db.query(CallParticipant).filter(CallParticipant.call_participant_id == call_participant_id).first()
    if not call_participant:
        return None
    db.delete(call_participant)
    db.commit()
    return call_participant

def get_call_participant_by_id(db: Session, call_participant_id: UUID):
    return db.query(CallParticipant).filter(CallParticipant.call_participant_id == call_participant_id).first()

def get_call_participant_by_call_id(db: Session, call_id: UUID):
    return db.query(CallParticipant).filter(CallParticipant.call_id == call_id).all()

def get_call_participant_by_user_id(db: Session, user_id: UUID):
    return db.query(CallParticipant).filter(CallParticipant.user_id == user_id).all()

def get_call_participant_by_program_id(db: Session, program_id: UUID):
    return db.query(CallParticipant).filter(CallParticipant.program_id == program_id).all()