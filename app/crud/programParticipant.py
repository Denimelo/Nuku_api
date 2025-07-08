from sqlalchemy.orm import Session
from uuid import UUID
from app.models.programParticipant import ProgramParticipant
from app.schemas.programParticipant import ProgramParticipantCreate, ProgramParticipantUpdate

def create_program_participant(db: Session, program_participant_in: ProgramParticipantCreate):
    program_participant = ProgramParticipant(**program_participant_in.dict())
    db.add(program_participant)
    db.commit()
    db.refresh(program_participant)
    return program_participant

def get_program_participant(db: Session, program_participant_id: UUID):
    return db.query(ProgramParticipant).filter(ProgramParticipant.program_participant_id == program_participant_id).first()

def get_program_participants(db: Session, skip: int = 0, limit: int = 100):
    return db.query(ProgramParticipant).offset(skip).limit(limit).all()

def update_program_participant(db: Session, program_participant_id: UUID, program_participant_in: ProgramParticipantUpdate):
    program_participant = db.query(ProgramParticipant).filter(ProgramParticipant.program_participant_id == program_participant_id).first()
    if not program_participant:
        return None
    for field, value in program_participant_in.dict(exclude_unset=True).items():
        setattr(program_participant, field, value)
    db.commit()
    db.refresh(program_participant)
    return program_participant

def delete_program_participant(db: Session, program_participant_id: UUID):
    program_participant = db.query(ProgramParticipant).filter(ProgramParticipant.program_participant_id == program_participant_id).first()
    if not program_participant:
        return None
    db.delete(program_participant)
    db.commit()
    return program_participant

def get_program_participant_by_id(db: Session, program_participant_id: UUID):
    return db.query(ProgramParticipant).filter(ProgramParticipant.program_participant_id == program_participant_id).first()

def get_program_participant_by_program_id(db: Session, program_id: UUID):
    return db.query(ProgramParticipant).filter(ProgramParticipant.program_id == program_id).all()

def get_program_participant_by_user_id(db: Session, user_id: UUID):
    return db.query(ProgramParticipant).filter(ProgramParticipant.user_id == user_id).all()