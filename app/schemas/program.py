from pydantic import BaseModel, UUID4
from typing import Optional
from datetime import date, datetime

class ProgramBase(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: date
    end_date: date
    max_participants: Optional[int] = None
    is_active: bool = True

class ProgramCreate(ProgramBase):
    created_by: UUID4

class ProgramUpdate(ProgramBase):
    name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None

class ProgramResponse(ProgramBase):
    program_id: UUID4
    created_by: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ProgramOut(ProgramBase):
    program_id: UUID4
    created_by: UUID4
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ProgramDelete(BaseModel):
    program_id: UUID4