from pydantic import BaseModel, UUID4
from typing import Optional
from datetime import datetime

class MessageAttachmentBase(BaseModel):
    file_name: str
    file_size: int
    content_type: str

class MessageAttachmentCreate(MessageAttachmentBase):
    file_url: str
    file_path: str
    original_file_name: str
    file_extension: Optional[str] = None
    image_width: Optional[int] = None
    image_height: Optional[int] = None

class MessageAttachmentResponse(MessageAttachmentBase):
    attachment_id: UUID4
    message_id: UUID4
    file_url: str
    original_file_name: str
    file_extension: Optional[str] = None
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    uploaded_at: datetime
    is_image: bool
    file_size_mb: float

    class Config:
        from_attributes = True