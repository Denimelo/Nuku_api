from pydantic import BaseModel, UUID4
from typing import Optional
from enum import Enum

class AttendanceStatus(str, Enum):
    registered = "registered"
    attended = "attended"
    no_show = "no_show"

class CallParticipantBase(BaseModel):
    call_id: UUID4
    entrepreneur_id: UUID4

class CallParticipantCreate(CallParticipantBase):
    attendance_status: AttendanceStatus = AttendanceStatus.registered
    feedback_rating: Optional[int] = None
    feedback_comment: Optional[str] = None

class CallParticipantResponse(CallParticipantBase):
    call_participant_id: UUID4
    attendance_status: AttendanceStatus
    feedback_rating: Optional[int] = None
    feedback_comment: Optional[str] = None

    class Config:
        from_attributes = True

class CallParticipantOut(CallParticipantBase):
    call_participant_id: UUID4
    attendance_status: AttendanceStatus
    feedback_rating: Optional[int] = None
    feedback_comment: Optional[str] = None

    class Config:
        from_attributes = True

class CallParticipantUpdate(BaseModel):
    attendance_status: Optional[AttendanceStatus] = None
    feedback_rating: Optional[int] = None
    feedback_comment: Optional[str] = None

    class Config:
        from_attributes = True

class CallParticipantDelete(BaseModel):
    call_participant_id: UUID4

    class Config:
        from_attributes = True