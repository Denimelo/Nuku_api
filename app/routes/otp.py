from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.auth import SendOTPRequest, SendOTPResponse, VerifyOTPRequest, VerifyOTPResponse
from app.crud.user import get_user_by_email
from app.crud.otp import create_otp, verify_otp
from app.models.otp import OTPType
from app.utils.email import send_otp_email
from app.config import settings

router = APIRouter(prefix="/otp", tags=["OTP"])

@router.post("/send", response_model=SendOTPResponse)
def send_otp_code(request: SendOTPRequest, db: Session = Depends(get_db)):
    """Envoyer un code OTP"""
    
    # Vérifier que l'utilisateur existe
    user = get_user_by_email(db, request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    # Valider le type OTP
    if request.otp_type not in [e.value for e in OTPType]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Type OTP invalide"
        )
    
    # Créer le code OTP
    otp = create_otp(
        db=db,
        user_id=user.user_id,
        email=user.email,
        otp_type=OTPType(request.otp_type)
    )
    
    # Envoyer par email
    full_name = f"{user.first_name} {user.last_name}"
    send_otp_email(
        to_email=user.email,
        full_name=full_name,
        otp_code=otp.otp_code,
        otp_type=request.otp_type
    )
    
    return SendOTPResponse(
        message="Code OTP envoyé avec succès",
        expires_in_minutes=settings.OTP_EXPIRY_MINUTES
    )

@router.post("/verify", response_model=VerifyOTPResponse)
def verify_otp_code(request: VerifyOTPRequest, db: Session = Depends(get_db)):
    """Vérifier un code OTP"""
    
    # Valider le type OTP
    if request.otp_type not in [e.value for e in OTPType]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Type OTP invalide"
        )
    
    # Vérifier le code
    is_valid, message = verify_otp(
        db=db,
        email=request.email,
        otp_code=request.otp_code,
        otp_type=OTPType(request.otp_type)
    )
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return VerifyOTPResponse(
        message="Code OTP vérifié avec succès",
        is_valid=True
    )