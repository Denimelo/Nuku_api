from sqlalchemy.orm import Session
from app.models.otp import OTP, OTPType
from app.utils.security import generate_otp_code, get_otp_expiry
from datetime import datetime
from uuid import UUID

def create_otp(
    db: Session, 
    user_id: UUID, 
    email: str, 
    otp_type: OTPType
) -> OTP:
    """Créer un nouveau code OTP"""
    # Invalider les anciens OTP non utilisés pour ce user/type
    db.query(OTP).filter(
        OTP.user_id == user_id,
        OTP.otp_type == otp_type,
        OTP.is_used == False
    ).update({"is_used": True})
    
    # Créer nouveau OTP
    otp_code = generate_otp_code()
    new_otp = OTP(
        user_id=user_id,
        email=email,
        otp_code=otp_code,
        otp_type=otp_type,
        expires_at=get_otp_expiry()
    )
    
    db.add(new_otp)
    db.commit()
    db.refresh(new_otp)
    return new_otp

def verify_otp(
    db: Session, 
    email: str, 
    otp_code: str, 
    otp_type: OTPType
) -> tuple[bool, str]:
    """Vérifier un code OTP"""
    otp = db.query(OTP).filter(
        OTP.email == email,
        OTP.otp_code == otp_code,
        OTP.otp_type == otp_type,
        OTP.is_used == False
    ).first()
    
    if not otp:
        return False, "Code OTP invalide"
    
    if otp.is_expired():
        return False, "Code OTP expiré"
    
    # Marquer comme utilisé
    otp.is_used = True
    db.commit()
    
    return True, "Code OTP valide"

def get_active_otp(
    db: Session, 
    user_id: UUID, 
    otp_type: OTPType
) -> OTP:
    """Récupérer un OTP actif"""
    return db.query(OTP).filter(
        OTP.user_id == user_id,
        OTP.otp_type == otp_type,
        OTP.is_used == False,
        OTP.expires_at > datetime.utcnow()
    ).first()