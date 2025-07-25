from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from uuid import UUID
from app.models.user import User, UserStatus
from app.utils.security import hash_password
from typing import Dict, Any, Optional

def create_user(db: Session, user_data: Dict[str, Any]) -> User:
    """Créer un utilisateur avec données dict (plus flexible)"""
    if "password_hash" not in user_data and "password" in user_data:
        user_data["password_hash"] = hash_password(user_data["password"])
        del user_data["password"]
    
    user = User(**user_data)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def get_user_by_id(db: Session, user_id: UUID) -> Optional[User]:
    return db.query(User).filter(User.user_id == user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(User).offset(skip).limit(limit).all()

def update_user(db: Session, user_id: UUID, update_data: Dict[str, Any]) -> Optional[User]:
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        return None
    
    for field, value in update_data.items():
        if hasattr(user, field):
            setattr(user, field, value)
    
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user

def update_user_password(db: Session, user_id: UUID, new_password: str) -> bool:
    """Mettre à jour le mot de passe d'un utilisateur"""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        return False
    
    user.password_hash = hash_password(new_password)
    user.is_temporary_password = False
    user.temporary_password_expiration = None
    user.updated_at = datetime.utcnow()
    
    db.commit()
    return True

def delete_user(db: Session, user_id: UUID) -> Optional[User]:
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        return None
    db.delete(user)
    db.commit()
    return user

def get_users_by_type(db: Session, user_type: str, status: Optional[str] = None):
    """Récupérer utilisateurs par type et statut"""
    query = db.query(User).filter(User.user_type == user_type)
    if status:
        query = query.filter(User.status == status)
    return query.all()