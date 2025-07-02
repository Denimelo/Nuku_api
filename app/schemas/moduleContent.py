from pydantic import BaseModel, UUID4
from typing import Optional
from enum import Enum
from datetime import datetime

class ContentType(str, Enum):
    video = "video"
    text = "text"
    pdf = "pdf"
    quiz = "quiz"

class ModuleContentBase(BaseModel):
    module_id: UUID4
    content_type: ContentType
    title: str
    content_url: Optional[str] = None
    duration_minutes: Optional[int] = None
    text_content: Optional[str] = None

class ModuleContentCreate(ModuleContentBase):
    pass

class ModuleContentResponse(ModuleContentBase):
    content_id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ModuleContentOut(ModuleContentBase):
    content_id: UUID4
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ModuleContentUpdate(BaseModel):
    title: Optional[str] = None
    content_type: Optional[ContentType] = None
    content_url: Optional[str] = None
    duration_minutes: Optional[int] = None
    text_content: Optional[str] = None

    class Config:
        from_attributes = True

class ModuleContentDelete(BaseModel):
    content_id: UUID4

    class Config:
        from_attributes = True