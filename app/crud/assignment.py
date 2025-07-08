from sqlalchemy.orm import Session
from uuid import UUID
from app.models.assignment import Assignment
from app.schemas.assignment import AssignmentCreate, AssignmentUpdate

def create_assignment(db: Session, assignment_in: AssignmentCreate):
    assignment = Assignment(**assignment_in.dict())
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment

def get_assignment(db: Session, assignment_id: UUID):
    return db.query(Assignment).filter(Assignment.assignment_id == assignment_id).first()

def get_assignments(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Assignment).offset(skip).limit(limit).all()

def update_assignment(db: Session, assignment_id: UUID, assignment_in: AssignmentUpdate):
    assignment = db.query(Assignment).filter(Assignment.assignment_id == assignment_id).first()
    if not assignment:
        return None
    for field, value in assignment_in.dict(exclude_unset=True).items():
        setattr(assignment, field, value)
    db.commit()
    db.refresh(assignment)
    return assignment

def delete_assignment(db: Session, assignment_id: UUID):
    assignment = db.query(Assignment).filter(Assignment.assignment_id == assignment_id).first()
    if not assignment:
        return None
    db.delete(assignment)
    db.commit()
    return assignment

def get_assignment_by_id(db: Session, assignment_id: UUID):
    return db.query(Assignment).filter(Assignment.assignment_id == assignment_id).first()

def get_assignments_by_program_id(db: Session, program_id: UUID):
    return db.query(Assignment).filter(Assignment.program_id == program_id).all()

def get_assignments_by_user_id(db: Session, user_id: UUID):
    return db.query(Assignment).filter(Assignment.user_id == user_id).all()

def get_assignments_by_module_id(db: Session, module_id: UUID):
    return db.query(Assignment).filter(Assignment.module_id == module_id).all()
