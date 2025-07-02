from pydantic import BaseModel, UUID4
from typing import Optional
from datetime import datetime

class CallBase(BaseModel):
    program_id: UUID4
    title: str
    description: Optional[str] = None
    scheduled_time: datetime
    duration_minutes: int
    expert_id: UUID4
    max_participants: Optional[int] = None
    meeting_url: str

class CallCreate(CallBase):
    pass

class CallUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    scheduled_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    meeting_url: Optional[str] = None

class CallResponse(CallBase):
    call_id: UUID4
    created_at: datetime

    class Config:
        from_attributes = True

class CallOut(CallBase):
    call_id: UUID4
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class CallDelete(BaseModel):
    call_id: UUID4

    class Config:
        from_attributes = True