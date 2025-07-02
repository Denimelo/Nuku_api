from pydantic import BaseModel, UUID4
from typing import Optional
from datetime import datetime, date

class AssignmentBase(BaseModel):
    module_id: UUID4
    title: str
    description: Optional[str] = None
    due_date: date
    max_points: int

class AssignmentCreate(AssignmentBase):
    created_by: UUID4

class AssignmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[date] = None
    max_points: Optional[int] = None

class AssignmentResponse(AssignmentBase):
    assignment_id: UUID4
    created_by: UUID4
    created_at: datetime

    class Config:
        from_attributes = True

class AssignmentOut(AssignmentBase):
    assignment_id: UUID4
    created_by: UUID4
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AssignmentDelete(BaseModel):
    assignment_id: UUID4

    class Config:
        from_attributes = True