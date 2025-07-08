from sqlalchemy.orm import Session
from uuid import UUID
from app.models.programExpert import ProgramExpert
from app.schemas.programExpert import ProgramExpertCreate, ProgramExpertUpdate

def create_program_expert(db: Session, program_expert_in: ProgramExpertCreate):
    program_expert = ProgramExpert(**program_expert_in.dict())
    db.add(program_expert)
    db.commit()
    db.refresh(program_expert)
    return program_expert

def get_program_expert(db: Session, program_expert_id: UUID):
    return db.query(ProgramExpert).filter(ProgramExpert.program_expert_id == program_expert_id).first()

def get_program_experts(db: Session, skip: int = 0, limit: int = 100):
    return db.query(ProgramExpert).offset(skip).limit(limit).all()

def update_program_expert(db: Session, program_expert_id: UUID, program_expert_in: ProgramExpertUpdate):
    program_expert = db.query(ProgramExpert).filter(ProgramExpert.program_expert_id == program_expert_id).first()
    if not program_expert:
        return None
    for field, value in program_expert_in.dict(exclude_unset=True).items():
        setattr(program_expert, field, value)
    db.commit()
    db.refresh(program_expert)
    return program_expert

def delete_program_expert(db: Session, program_expert_id: UUID):
    program_expert = db.query(ProgramExpert).filter(ProgramExpert.program_expert_id == program_expert_id).first()
    if not program_expert:
        return None
    db.delete(program_expert)
    db.commit()
    return program_expert

def get_program_expert_by_id(db: Session, program_expert_id: UUID):
    return db.query(ProgramExpert).filter(ProgramExpert.program_expert_id == program_expert_id).first()

def get_program_expert_by_program_id(db: Session, program_id: UUID):
    return db.query(ProgramExpert).filter(ProgramExpert.program_id == program_id).all()