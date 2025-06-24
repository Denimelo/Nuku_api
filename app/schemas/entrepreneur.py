from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import date, datetime
from enum import Enum
from app.schemas.user import UserCreate
from pydantic import UUID4
from app.schemas.user import UserResponse



class ValidationStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class EntrepreneurBase(BaseModel):
    company_name: str
    company_registration_number: Optional[str] = None
    company_description: Optional[str] = None
    industry_sector: Optional[str] = None
    founding_date: Optional[date] = None
    number_of_employees: Optional[int] = None
    annual_revenue: Optional[float] = None
    has_raised_funds: Optional[bool] = False
    amount_raised: Optional[float] = None
    wants_to_raise_funds: Optional[bool] = False
    desired_funding_amount: Optional[float] = None


class EntrepreneurCreate(EntrepreneurBase):
    user: 'UserCreate'

class EntrepreneurUpdate(EntrepreneurBase):
    company_name: Optional[str] = None
    company_registration_number: Optional[str] = None
    company_description: Optional[str] = None
    industry_sector: Optional[str] = None
    founding_date: Optional[date] = None
    number_of_employees: Optional[int] = None
    annual_revenue: Optional[float] = None
    has_raised_funds: Optional[bool] = None
    amount_raised: Optional[float] = None
    wants_to_raise_funds: Optional[bool] = None
    desired_funding_amount: Optional[float] = None


class EntrepreneurResponse(BaseModel):
    entrepreneur_id: UUID4
    user: UserResponse
    company_name: str
    company_registration_number: Optional[str]
    company_description: Optional[str]
    industry_sector: Optional[str]
    founding_date: Optional[date]
    number_of_employees: Optional[int]
    annual_revenue: Optional[float]
    has_raised_funds: Optional[bool]
    amount_raised: Optional[float]
    wants_to_raise_funds: Optional[bool]
    desired_funding_amount: Optional[float]
    validation_status: str
    validation_date: Optional[datetime]
    validated_by: Optional[UUID4]

class EntrepreneurOut(EntrepreneurBase):
    entrepreneur_id: UUID

    class Config:
        from_attributes = True
