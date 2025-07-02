from pydantic import BaseModel, UUID4
from typing import Optional
from datetime import datetime

class AssignmentSubmissionBase(BaseModel):
    assignment_id: UUID4
    entrepreneur_id: UUID4
    submission_text: Optional[str] = None
    submission_url: Optional[str] = None

class AssignmentSubmissionCreate(AssignmentSubmissionBase):
    pass

class AssignmentSubmissionResponse(AssignmentSubmissionBase):
    submission_id: UUID4
    submission_date: datetime
    grade: Optional[float] = None
    feedback: Optional[str] = None
    graded_by: Optional[UUID4] = None
    graded_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AssignmentSubmissionOut(AssignmentSubmissionBase):
    submission_id: UUID4
    submission_date: datetime
    grade: Optional[float] = None
    feedback: Optional[str] = None
    graded_by: Optional[UUID4] = None
    graded_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AssignmentSubmissionUpdate(BaseModel):
    submission_text: Optional[str] = None
    submission_url: Optional[str] = None
    grade: Optional[float] = None
    feedback: Optional[str] = None
    graded_by: Optional[UUID4] = None
    graded_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AssignmentSubmissionDelete(BaseModel):
    submission_id: UUID4

    class Config:
        from_attributes = True