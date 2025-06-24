from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from app.config import settings
from typing import Optional
import secrets
import string

# Contexte de hashage sécurisé
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Clé et durée de validité du token
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = settings.ACCESS_TOKEN_EXPIRE_HOURS


# 🔐 1. Hashage du mot de passe
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


# 🔐 2. Vérification du mot de passe
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# 🪪 3. Création d’un token d’accès JWT
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# 🧪 4. Décodage d’un token JWT (authentification)
def verify_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


# 🔑 5. Génération de mot de passe temporaire sécurisé
def generate_temporary_password(length: int = 10) -> str:
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))

# 📧 6. Création d’un token de validation d’email
def create_email_validation_token(user_id: str, hours: int = 6):
    expire = timedelta(hours=hours)
    return create_access_token({"sub": user_id, "scope": "email_validation"}, expire)

