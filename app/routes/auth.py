from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.auth import LoginRequest
from app.crud.entrepreneur import create_entrepreneur
from app.crud.user import get_user_by_email
from app.database import get_db
from app.schemas.entrepreneur import EntrepreneurResponse, EntrepreneurCreate
from app.utils.security import create_access_token, hash_password, verify_password
from app.models.user import User, UserStatus
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
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    user = get_user_by_email(db, login_data.email)
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Identifiants incorrects")

    if user.status != UserStatus.active:
        raise HTTPException(status_code=403, detail="Compte inactif")
    
    # if user.must_change_password:
    #     raise HTTPException(status_code=403, detail="Veuillez changer votre mot de passe temporaire"
    # )

    token = create_access_token({"sub": str(user.user_id)})
    return {"access_token": token, "token_type": "bearer"}

@router.get("/activate-account")
def activate_account(token: str, db: Session = Depends(get_db)):
    from app.utils.security import decode_token
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=400, detail="Token invalide")

        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur introuvable")

        user.status = UserStatus.active
        db.commit()

        return {"message": "Compte activé avec succès"}
    except Exception:
        raise HTTPException(status_code=400, detail="Token invalide ou expiré")


@router.post("/change-password")
def change_password(
    current_password: str,
    new_password: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if not verify_password(current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Mot de passe actuel incorrect")

    user = db.query(User).filter(User.user_id == current_user.user_id).first()
    print("Ancien hash:", user.password_hash)
    user.password_hash = hash_password(new_password)
    print("Nouveau hash:", user.password_hash)

    user.is_temporary_password = False  # ✅ si tu veux le désactiver après changement
    db.commit()
    return {"message": "Mot de passe changé avec succès"}
