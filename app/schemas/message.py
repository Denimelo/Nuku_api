from pydantic import BaseModel, UUID4
from typing import Optional
from datetime import datetime

class MessageBase(BaseModel):
    sender_id: UUID4
    receiver_id: UUID4
    message_text: str
    program_id: Optional[UUID4] = None

class MessageCreate(MessageBase):
    pass

class MessageResponse(MessageBase):
    message_id: UUID4
    sent_at: datetime
    read_status: bool

    class Config:
        from_attributes = True

class MessageOut(MessageBase):
    message_id: UUID4
    sent_at: datetime
    read_status: bool

    class Config:
        from_attributes = True

class MessageUpdate(BaseModel):
    message_text: Optional[str] = None
    read_status: Optional[bool] = None

    class Config:
        from_attributes = True

class MessageDelete(BaseModel):
    message_id: UUID4

    class Config:
        from_attributes = True