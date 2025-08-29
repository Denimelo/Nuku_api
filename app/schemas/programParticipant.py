from pydantic import BaseModel, UUID4
from typing import Optional
from datetime import date
from enum import Enum

class CompletionStatus(str, Enum):
    in_progress = "in_progress"
    completed = "completed"
    dropped = "dropped"

class ProgramParticipantBase(BaseModel):
    program_id: UUID4
    entrepreneur_id: UUID4

class ProgramParticipantCreate(ProgramParticipantBase):
    pass

class ProgramParticipantResponse(ProgramParticipantBase):
    participant_id: UUID4
    enrollment_request_date: date
    completion_status: CompletionStatus
    completion_date: Optional[date] = None

    class Config:
        from_attributes = True

class ProgramParticipantOut(ProgramParticipantBase):
    participant_id: UUID4
    enrollment_request_date: date
    completion_status: CompletionStatus
    completion_date: Optional[date] = None

    class Config:
        from_attributes = True

class ProgramParticipantUpdate(BaseModel):
    completion_status: Optional[CompletionStatus] = None
    completion_date: Optional[date] = None

    class Config:
        from_attributes = True

class ProgramParticipantDelete(BaseModel):
    participant_id: UUID4

    class Config:
        from_attributes = True