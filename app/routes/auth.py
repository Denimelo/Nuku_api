from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.dependencies import get_current_user
from app.schemas.auth import (
    LoginRequest, LoginResponse, RegisterRequest, RegisterResponse,
    RegisterWithOTPRequest, ResetPasswordRequest, ResetPasswordResponse,
    ResetPasswordWithOTPRequest, ChangePasswordRequest
)
from app.crud.user import get_user_by_email, create_user, update_user_password
from app.crud.entrepreneur import create_entrepreneur_profile
from app.crud.otp import create_otp, verify_otp
from app.models.user import User, UserType, UserStatus
from app.models.otp import OTPType
from app.utils.security import (
    verify_password, hash_password, create_access_token, verify_access_token
)
from app.utils.email import send_entrepreneur_registration_confirmation, send_otp_email, send_admin_entrepreneur_notification_email
from app.config import settings
from uuid import uuid4
from datetime import datetime

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=RegisterResponse)
def register_entrepreneur_step1(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    🚀 Étape 1 : Inscription entrepreneur (envoie OTP pour vérification email)
    """
    # Vérifier si l'utilisateur existe déjà
    existing_user = get_user_by_email(db, request.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un compte avec cet email existe déjà"
        )
    
    # Créer l'utilisateur (statut pending)
    user_data = {
        "user_id": uuid4(),
        "email": request.email,
        "password_hash": hash_password(request.password),
        "first_name": request.first_name,
        "last_name": request.last_name,
        "phone": request.phone,
        "user_type": UserType.entrepreneur,
        "status": UserStatus.pending
    }
    
    user = create_user(db, user_data)
    
    # Générer et envoyer OTP
    otp = create_otp(
        db=db,
        user_id=user.user_id,
        email=user.email,
        otp_type=OTPType.email_verification
    )
    
    full_name = f"{user.first_name} {user.last_name}"
    send_otp_email(
        to_email=user.email,
        full_name=full_name,
        otp_code=otp.otp_code,
        otp_type="email_verification"
    )
    
    return RegisterResponse(
        message=f"Inscription initiée. Un code de vérification a été envoyé à {request.email}",
        user_id=str(user.user_id)
    )

@router.post("/register/verify", response_model=RegisterResponse)
def register_entrepreneur_step2(request: RegisterWithOTPRequest, db: Session = Depends(get_db)):
    """
    ✅ Étape 2 : Finaliser inscription entrepreneur avec OTP
    """
    # Vérifier le code OTP
    is_valid, message = verify_otp(
        db=db,
        email=request.email,
        otp_code=request.otp_code,
        otp_type=OTPType.email_verification
    )
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    # Récupérer l'utilisateur
    user = get_user_by_email(db, request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    # Activer le compte
    user.status = UserStatus.active
    user.updated_at = datetime.utcnow()
    
    # Créer le profil entrepreneur avec données du formulaire
    entrepreneur_data = {
        "user_id": user.user_id,
        "company_name": request.company_name,
        "company_description": request.company_description,
        "industry_sector": request.industry_sector,
        "number_of_employees": request.number_of_employees,
        "company_not_created": request.company_not_created,
        "company_recently_created": request.company_recently_created,
        "company_established": request.company_established,
    }
    
    entrepreneur = create_entrepreneur_profile(db, entrepreneur_data)
    
    # Envoyer notification à l'admin
    send_admin_entrepreneur_notification_email(entrepreneur, user)

    # 🆕 Envoyer confirmation à l'entrepreneur
    send_entrepreneur_registration_confirmation(
        to_email=user.email,
        full_name=f"{user.first_name} {user.last_name}",
        company_name=entrepreneur.company_name
    )
    
    db.commit()
    
    return RegisterResponse(
        message="Inscription finalisée avec succès. Votre profil est en attente de validation.",
        user_id=str(user.user_id)
    )

@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    🔑 Connexion utilisateur
    """
    user = get_user_by_email(db, request.email)
    
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect"
        )
    
    if user.status == UserStatus.suspended:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte suspendu"
        )
    
    if user.status == UserStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte en attente d'activation"
        )
    
    # Mettre à jour la dernière connexion
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Créer le token
    access_token = create_access_token(data={"sub": str(user.user_id)})
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=str(user.user_id),
        user_type=user.user_type.value
    )

@router.post("/reset-password", response_model=ResetPasswordResponse)
def reset_password_step1(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    🔄 Étape 1 : Demande de réinitialisation (envoie OTP)
    """
    user = get_user_by_email(db, request.email)
    if not user:
        # Pas d'erreur pour éviter l'énumération d'emails
        return ResetPasswordResponse(
            message="Si cet email existe, un code de vérification a été envoyé."
        )
    
    # Générer et envoyer OTP
    otp = create_otp(
        db=db,
        user_id=user.user_id,
        email=user.email,
        otp_type=OTPType.password_reset
    )
    
    full_name = f"{user.first_name} {user.last_name}"
    send_otp_email(
        to_email=user.email,
        full_name=full_name,
        otp_code=otp.otp_code,
        otp_type="password_reset"
    )
    
    return ResetPasswordResponse(
        message="Si cet email existe, un code de vérification a été envoyé."
    )

@router.post("/reset-password/verify", response_model=ResetPasswordResponse)
def reset_password_step2(request: ResetPasswordWithOTPRequest, db: Session = Depends(get_db)):
    """
    ✅ Étape 2 : Réinitialiser mot de passe avec OTP
    """
    # Vérifier le code OTP
    is_valid, message = verify_otp(
        db=db,
        email=request.email,
        otp_code=request.otp_code,
        otp_type=OTPType.password_reset
    )
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    # Réinitialiser le mot de passe
    user = get_user_by_email(db, request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    update_user_password(db, user.user_id, request.new_password)
    
    return ResetPasswordResponse(
        message="Mot de passe réinitialisé avec succès"
    )

@router.post("/change-password")
def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    🔄 Changer mot de passe (utilisateur connecté)
    """
    if not verify_password(request.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mot de passe actuel incorrect"
        )
    
    # Si c'était la première connexion, marquer comme terminée
    if current_user.is_first_connection:
        current_user.is_first_connection = False
        current_user.is_temporary_password = False
    
    update_user_password(db, current_user.user_id, request.new_password)
    
    return {"message": "Mot de passe modifié avec succès"}

@router.post("/complete-first-login", dependencies=[Depends(get_current_user)])
def complete_first_login(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Marquer la première connexion comme terminée"""
    
    if not current_user.is_first_connection:
        raise HTTPException(status_code=400, detail="La première connexion a déjà été complétée")
    
    # Mettre à jour les champs
    current_user.is_first_connection = False
    current_user.is_temporary_password = False
    current_user.last_login = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Première connexion complétée avec succès"}

@router.get("/me")
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    👤 Récupérer les informations de l'utilisateur connecté
    """
    return {
        "user_id": str(current_user.user_id),
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "user_type": current_user.user_type.value,
        "status": current_user.status.value,
        "phone": current_user.phone,
        "created_at": current_user.created_at,
        "last_login": current_user.last_login,
        "is_first_connection": current_user.is_first_connection,
        "is_temporary_password": current_user.is_temporary_password
    }