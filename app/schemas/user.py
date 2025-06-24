from pydantic import BaseModel, EmailStr
from uuid import UUID
from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import UUID4


class UserType(str, Enum):
    entrepreneur = "entrepreneur"
    expert = "expert"
    admin = "admin"

class UserStatus(str, Enum):
    pending = "pending"
    active = "active"
    suspended = "suspended"


class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None


class UserCreate(UserBase):
    password: str
    user_type: UserType

class UserUpdate(UserBase):
    password: Optional[str] = None
    user_type: Optional[UserType] = None
    status: Optional[UserStatus] = None

class UserResponse(BaseModel):
    user_id: UUID4
    email: EmailStr
    first_name: str
    last_name: str
    phone: Optional[str]
    address: Optional[str]
    city: Optional[str]
    country: Optional[str]
    postal_code: Optional[str]
    user_type: str
    status: str
    created_at: datetime

class UserOut(UserBase):
    user_id: UUID
    user_type: UserType
    status: UserStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True
