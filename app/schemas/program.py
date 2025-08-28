from pydantic import BaseModel, UUID4
from typing import List, Optional
from datetime import date, datetime
from enum import Enum

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

class CompletionStatusSchema(str, Enum):
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
    enrollment_request_date: Optional[datetime] = None
    completion_status: CompletionStatusSchema
    completion_date: Optional[datetime] = None

    class Config:
        from_attributes = True

class ProgramWithParticipation(ProgramResponse):
    """Programme avec info de participation de l'entrepreneur connecté"""
    is_enrolled: bool = False
    enrollment_request_date: Optional[datetime] = None
    completion_status: Optional[CompletionStatusSchema] = None
    participants_count: int = 0
    available_spots: Optional[int] = None

class ProgramStats(BaseModel):
    """Statistiques d'un programme"""
    total_participants: int
    active_participants: int
    completed_participants: int
    dropped_participants: int
    completion_rate: float

class EntrepreneurProgramSummary(BaseModel):
    """Résumé des programmes d'un entrepreneur"""
    total_programs: int
    active_programs: int
    completed_programs: int
    programs: List[ProgramParticipantResponse]