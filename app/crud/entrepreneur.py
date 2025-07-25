from sqlalchemy.orm import Session
from app.models.entrepreneur import Entrepreneur, ValidationStatus
from app.models.user import User
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime

def create_entrepreneur_profile(db: Session, entrepreneur_data: Dict[str, Any]) -> Entrepreneur:
    """Créer un profil entrepreneur (utilisateur déjà créé)"""
    entrepreneur = Entrepreneur(**entrepreneur_data)
    db.add(entrepreneur)
    db.commit()
    db.refresh(entrepreneur)
    return entrepreneur

def get_entrepreneur_by_user_id(db: Session, user_id: UUID) -> Optional[Entrepreneur]:
    return db.query(Entrepreneur).filter(Entrepreneur.user_id == user_id).first()

def get_entrepreneur_by_id(db: Session, entrepreneur_id: UUID) -> Optional[Entrepreneur]:
    return db.query(Entrepreneur).filter(Entrepreneur.entrepreneur_id == entrepreneur_id).first()

def get_entrepreneurs_by_status(db: Session, status: ValidationStatus) -> list[Entrepreneur]:
    """Récupérer entrepreneurs par statut de validation"""
    return db.query(Entrepreneur).filter(Entrepreneur.validation_status == status).all()

def update_entrepreneur_validation(
    db: Session, 
    entrepreneur_id: UUID, 
    status: ValidationStatus, 
    validated_by: UUID
) -> Optional[Entrepreneur]:
    """Valider/rejeter un entrepreneur"""
    entrepreneur = db.query(Entrepreneur).filter(Entrepreneur.entrepreneur_id == entrepreneur_id).first()
    if not entrepreneur:
        return None
    
    entrepreneur.validation_status = status
    entrepreneur.validation_date = datetime.utcnow()
    entrepreneur.validated_by = validated_by
    
    db.commit()
    db.refresh(entrepreneur)
    return entrepreneur

def update_entrepreneur_profile(
    db: Session, 
    entrepreneur_id: UUID, 
    update_data: Dict[str, Any]
) -> Optional[Entrepreneur]:
    """Mettre à jour profil entrepreneur"""
    entrepreneur = db.query(Entrepreneur).filter(Entrepreneur.entrepreneur_id == entrepreneur_id).first()
    if not entrepreneur:
        return None
    
    for field, value in update_data.items():
        if hasattr(entrepreneur, field):
            setattr(entrepreneur, field, value)
    
    db.commit()
    db.refresh(entrepreneur)
    return entrepreneur

def get_entrepreneurs_with_users(db: Session, skip: int = 0, limit: int = 100):
    """Récupérer entrepreneurs avec leurs infos utilisateur"""
    return db.query(Entrepreneur).join(User).offset(skip).limit(limit).all()