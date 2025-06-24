from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.crud.entrepreneur import create_entrepreneur
from app.crud.user import get_user_by_email
from app.database import get_db
from app.schemas.entrepreneur import EntrepreneurResponse, EntrepreneurCreate
from app.utils.security import create_access_token, verify_password
from app.models.user import UserStatus
from app.utils.email import send_admin_entrepreneur_notification_email
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup/entrepreneur", response_model=EntrepreneurResponse)
def register_entrepreneur(payload: EntrepreneurCreate, db: Session = Depends(get_db)):
    if get_user_by_email(db, payload.user.email):
        raise HTTPException(status_code=400, detail="Email déjà utilisé")

    entrepreneur = create_entrepreneur(db, payload)

    # 📨 Notifier l'admin
    send_admin_entrepreneur_notification_email(entrepreneur, entrepreneur.user)

    return entrepreneur


@router.post("/login")
def login(email: str, password: str, db: Session = Depends(get_db)):
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Identifiants incorrects")

    if user.status != UserStatus.active:
        raise HTTPException(status_code=403, detail="Compte inactif")

    token = create_access_token({"sub": str(user.user_id)})
    return {"access_token": token, "token_type": "bearer"}