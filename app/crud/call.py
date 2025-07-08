from sqlalchemy.orm import Session
from uuid import UUID

from app.models.call import Call
from app.schemas.call import CallCreate, CallUpdate

def create_call(db: Session, call_in: CallCreate):
    call = Call(**call_in.dict())
    db.add(call)
    db.commit()
    db.refresh(call)
    return call

def get_call(db: Session, call_id: UUID):
    return db.query(Call).filter(Call.call_id == call_id).first()

def get_calls(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Call).offset(skip).limit(limit).all()

def update_call(db: Session, call_id: UUID, call_in: CallUpdate):
    call = db.query(Call).filter(Call.call_id == call_id).first()
    if not call:
        return None
    for field, value in call_in.dict(exclude_unset=True).items():
        setattr(call, field, value)
    db.commit()
    db.refresh(call)
    return call

def delete_call(db: Session, call_id: UUID):
    call = db.query(Call).filter(Call.call_id == call_id).first()
    if not call:
        return None
    db.delete(call)
    db.commit()
    return call

def get_call_by_id(db: Session, call_id: UUID):
    return db.query(Call).filter(Call.call_id == call_id).first()

def get_calls_by_program_id(db: Session, program_id: UUID):
    return db.query(Call).filter(Call.program_id == program_id).all()

def get_calls_by_user_id(db: Session, user_id: UUID):
    return db.query(Call).filter(Call.user_id == user_id).all()

def get_calls_by_module_id(db: Session, module_id: UUID):
    return db.query(Call).filter(Call.module_id == module_id).all()