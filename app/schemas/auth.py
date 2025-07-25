from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

# 🆕 Schémas OTP
class SendOTPRequest(BaseModel):
    email: EmailStr
    otp_type: str

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp_code: str
    otp_type: str

class RegisterRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    password: str

class RegisterWithOTPRequest(BaseModel):
    # Infos utilisateur
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    password: str
    otp_code: str
    
    # 🏢 Infos entreprise (obligatoires)
    company_name: str
    company_description: Optional[str] = None
    industry_sector: Optional[str] = None
    
    # 📈 Données économiques (optionnelles)
    number_of_employees: Optional[int] = None
    annual_revenue: Optional[float] = None
    founding_date: Optional[date] = None
    company_registration_number: Optional[str] = None
    
    # 💰 Financement (optionnel)
    has_raised_funds: Optional[bool] = False
    amount_raised: Optional[float] = None
    wants_to_raise_funds: Optional[bool] = False
    desired_funding_amount: Optional[float] = None
    
    # 🔘 Niveau de maturité (un seul doit être True)
    company_not_created: Optional[bool] = False
    company_recently_created: Optional[bool] = False
    company_established: Optional[bool] = False

class ResetPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordWithOTPRequest(BaseModel):
    email: EmailStr
    otp_code: str
    new_password: str

# Réponses
class SendOTPResponse(BaseModel):
    message: str
    expires_in_minutes: int

class VerifyOTPResponse(BaseModel):
    message: str
    is_valid: bool

class RegisterResponse(BaseModel):
    message: str
    user_id: Optional[str] = None

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    user_type: str

class ResetPasswordResponse(BaseModel):
    message: str