from pydantic import EmailStr
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "NUKU API"
    API_V1_STR: str = "/api/v1"
    
    # Base de données
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str 
    POSTGRES_HOST: str
    POSTGRES_PORT: str = "5432"

    # Sécurité
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_HOURS: int = 6

    # Email
    SMTP_SERVER: str
    SMTP_PORT: int
    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    EMAIL_FROM: EmailStr
    EMAIL_FROM_NAME: Optional[str]

    # Admin Infos
    DEFAULT_ADMIN_EMAIL: EmailStr
    DEFAULT_ADMIN_PASSWORD: str

    # URLs
    FRONTEND_URL: str
    ADMIN_URL: str

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
