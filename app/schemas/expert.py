from pydantic import BaseModel, HttpUrl
from typing import Optional
from uuid import UUID
from app.schemas.user import UserResponse, UserCreate


class ExpertBase(BaseModel):
    specialization: str
    years_of_experience: Optional[int] = None
    linkedin_profile: Optional[HttpUrl] = None
    cv_url: Optional[HttpUrl] = None
    bio: Optional[str] = None
    hourly_rate: Optional[int] = None
    is_active: Optional[bool] = True


class ExpertCreate(ExpertBase):
    user: UserCreate

class ExpertUpdate(ExpertBase):
    specialization: Optional[str] = None
    years_of_experience: Optional[int] = None
    linkedin_profile: Optional[HttpUrl] = None
    cv_url: Optional[HttpUrl] = None
    bio: Optional[str] = None
    hourly_rate: Optional[int] = None
    is_active: Optional[bool] = None

class ExpertResponse(BaseModel):
    expert_id: UUID
    user: UserResponse
    specialization: str
    years_of_experience: Optional[int] = None
    linkedin_profile: Optional[HttpUrl] = None
    cv_url: Optional[HttpUrl] = None
    bio: Optional[str] = None
    hourly_rate: Optional[int] = None
    is_active: bool

class ExpertOut(ExpertBase):
    expert_id: UUID

    class Config:
        from_attributes = True
