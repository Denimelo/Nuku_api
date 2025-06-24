from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.orm import Session
from app.utils.security import verify_access_token
from app.database import SessionLocal
from app.models.user import User, UserType


# Middleware d'extraction du token
oauth2_scheme = HTTPBearer()


# 📦 Récupération de la DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 🔐 Fonction de base : récupérer l'utilisateur courant à partir du token
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials
    payload = verify_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur non identifié dans le token",
        )

    user = db.query(User).filter(User.user_id == user_id).first()

    if not user or user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Utilisateur non autorisé ou inactif",
        )

    return user

def require_admin(user: User = Depends(get_current_user)):
    if user.user_type != UserType.admin:
        raise HTTPException(status_code=403, detail="Accès réservé à l'administrateur.")
    return user

def require_expert(user: User = Depends(get_current_user)):
    if user.user_type != UserType.expert:
        raise HTTPException(status_code=403, detail="Accès réservé aux experts.")
    return user

def require_entrepreneur(user: User = Depends(get_current_user)):
    if user.user_type != UserType.entrepreneur:
        raise HTTPException(status_code=403, detail="Accès réservé aux entrepreneurs.")
    return user
