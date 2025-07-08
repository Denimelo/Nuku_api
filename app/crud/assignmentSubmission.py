from sqlalchemy.orm import Session
from uuid import UUID
from app.models.assignmentSubmission import AssignmentSubmission
from app.schemas.assignmentSubmission import AssignmentSubmissionCreate, AssignmentSubmissionUpdate

def create_assignment_submission(db: Session, assignment_submission_in: AssignmentSubmissionCreate):
    assignment_submission = AssignmentSubmission(**assignment_submission_in.dict())
    db.add(assignment_submission)
    db.commit()
    db.refresh(assignment_submission)
    return assignment_submission

def get_assignment_submission(db: Session, assignment_submission_id: UUID):
    return db.query(AssignmentSubmission).filter(AssignmentSubmission.assignment_submission_id == assignment_submission_id).first()

def get_assignment_submissions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(AssignmentSubmission).offset(skip).limit(limit).all()

def update_assignment_submission(db: Session, assignment_submission_id: UUID, assignment_submission_in: AssignmentSubmissionUpdate):
    assignment_submission = db.query(AssignmentSubmission).filter(AssignmentSubmission.assignment_submission_id == assignment_submission_id).first()
    if not assignment_submission:
        return None
    for field, value in assignment_submission_in.dict(exclude_unset=True).items():
        setattr(assignment_submission, field, value)
    db.commit()
    db.refresh(assignment_submission)
    return assignment_submission

def delete_assignment_submission(db: Session, assignment_submission_id: UUID):
    assignment_submission = db.query(AssignmentSubmission).filter(AssignmentSubmission.assignment_submission_id == assignment_submission_id).first()
    if not assignment_submission:
        return None
    db.delete(assignment_submission)
    db.commit()
    return assignment_submission

def get_assignment_submission_by_id(db: Session, assignment_submission_id: UUID):
    return db.query(AssignmentSubmission).filter(AssignmentSubmission.assignment_submission_id == assignment_submission_id).first()

def get_assignment_submissions_by_assignment_id(db: Session, assignment_id: UUID):
    return db.query(AssignmentSubmission).filter(AssignmentSubmission.assignment_id == assignment_id).all()

def get_assignment_submissions_by_user_id(db: Session, user_id: UUID):
    return db.query(AssignmentSubmission).filter(AssignmentSubmission.user_id == user_id).all()

def get_assignment_submissions_by_program_id(db: Session, program_id: UUID):
    return db.query(AssignmentSubmission).filter(AssignmentSubmission.program_id == program_id).all()