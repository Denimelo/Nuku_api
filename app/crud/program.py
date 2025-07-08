from sqlalchemy.orm import Session
from uuid import UUID
from ..models.program import Program
from ..schemas.program import ProgramCreate, ProgramUpdate

def create_program(db: Session, program_in: ProgramCreate):
    program = Program(**program_in.dict())
    db.add(program)
    db.commit()
    db.refresh(program)
    return program

def get_program(db: Session, program_id: UUID):
    return db.query(Program).filter(Program.program_id == program_id).first()

def get_all_programs(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Program).offset(skip).limit(limit).all()

def update_program(db: Session, program_id: UUID, program_in: ProgramUpdate):
    program = db.query(Program).filter(Program.program_id == program_id).first()
    if not program:
        return None
    for field, value in program_in.dict(exclude_unset=True).items():
        setattr(program, field, value)
    db.commit()
    db.refresh(program)
    return program

def delete_program(db: Session, program_id: UUID):
    program = db.query(Program).filter(Program.program_id == program_id).first()
    if not program:
        return None
    db.delete(program)
    db.commit()
    return program

def get_program_by_id(db: Session, program_id: UUID):
    return db.query(Program).filter(Program.program_id == program_id).first()

def get_programs_by_user_id(db: Session, user_id: UUID):
    return db.query(Program).filter(Program.user_id == user_id).all()

def get_programs_by_entrepreneur_id(db: Session, entrepreneur_id: UUID):
    return db.query(Program).filter(Program.entrepreneur_id == entrepreneur_id).all()

def get_programs_by_expert_id(db: Session, expert_id: UUID):
    return db.query(Program).filter(Program.expert_id == expert_id).all()

def get_programs_by_call_id(db: Session, call_id: UUID):
    return db.query(Program).filter(Program.call_id == call_id).all()