from pydantic import BaseModel, EmailStr

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class ActivateAccountRequest(BaseModel):
    token: str

class RegisterRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    password: str

class RegisterResponse(BaseModel):
    message: str
    user_id: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str

class ActivateAccountResponse(BaseModel):
    message: str


