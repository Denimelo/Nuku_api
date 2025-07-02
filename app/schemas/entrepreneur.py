from pydantic import BaseModel, HttpUrl
from typing import Optional
from uuid import UUID
from datetime import date, datetime
from enum import Enum
from app.schemas.user import UserCreate, UserResponse
from pydantic import UUID4

class ValidationStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class EntrepreneurBase(BaseModel):
    # Champs existants
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

    # 📎 Pièces jointes
    identity_card_url: Optional[HttpUrl] = None
    company_logo_url: Optional[HttpUrl] = None
    registration_document_url: Optional[HttpUrl] = None
    professional_card_url: Optional[HttpUrl] = None

    # 🔘 Niveau de maturité
    company_not_created: Optional[bool] = False
    company_recently_created: Optional[bool] = False
    company_established: Optional[bool] = False

class EntrepreneurCreate(EntrepreneurBase):
    user: UserCreate

class EntrepreneurUpdate(EntrepreneurBase):
    company_name: Optional[str] = None

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

    # Pièces jointes
    identity_card_url: Optional[HttpUrl]
    company_logo_url: Optional[HttpUrl]
    registration_document_url: Optional[HttpUrl]
    professional_card_url: Optional[HttpUrl]

    # Niveau
    company_not_created: Optional[bool]
    company_recently_created: Optional[bool]
    company_established: Optional[bool]

    validation_status: str
    validation_date: Optional[datetime]
    validated_by: Optional[UUID4]

class EntrepreneurOut(EntrepreneurBase):
    entrepreneur_id: UUID

    class Config:
        from_attributes = True
