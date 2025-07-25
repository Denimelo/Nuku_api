from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from app.crud.notification import create_notification
from app.models.notification import TypeNotification
from app.schemas.notification import NotificationCreate
from app.database import get_db
from app.models.user import User, UserStatus
from app.models.expert import Expert
from app.models.entrepreneur import Entrepreneur
from app.schemas.user import UserResponse
from app.schemas.entrepreneur import EntrepreneurResponse
from app.schemas.expert import ExpertCreate, ExpertResponse
from app.crud.user import get_user_by_email, get_user_by_id
from app.crud.expert import create_expert, get_expert_by_id
from app.crud.entrepreneur import Entrepreneur, get_entrepreneur_by_id
from app.auth.dependencies import get_current_user, require_admin
from app.utils.email import send_expert_welcome_email, send_entrepreneur_validation_email, send_entrepreneur_rejection_email
from app.utils.security import generate_temporary_password
from app.utils.security import generate_temporary_password
from typing import List
from datetime import datetime


# Router pour les opérations administratives
router = APIRouter(prefix="/admin", tags=["Admin"])

# 🔍 Créer un expert
@router.post("/experts", response_model=ExpertResponse, dependencies=[Depends(require_admin)])
def admin_create_expert(data: ExpertCreate, db: Session = Depends(get_db)):
    if get_user_by_email(db, data.user.email):
        raise HTTPException(status_code=400, detail="Email déjà utilisé")

    temp_password = generate_temporary_password()
    expert = create_expert(db, data, temp_password)

    # Envoi de l'email de bienvenue à l'expert
    send_expert_welcome_email(expert.user.email, f"{expert.user.first_name} {expert.user.last_name}", temp_password)

    # Notification
    create_notification(db, NotificationCreate(
        user_id=expert.user.user_id,
        user_type="expert",
        titre="Bienvenue sur NUKU",
        message="Votre compte a été créé. Connectez-vous avec le mot de passe temporaire envoyé par e-mail.",
        type=TypeNotification.success
    ))
    
    return expert


# 🔍 Valider un entrepreneur
@router.put("/entrepreneurs/{entrepreneur_id}/validate", dependencies=[Depends(require_admin)])
def validate_entrepreneur(entrepreneur_id: UUID, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    from app.models.entrepreneur import Entrepreneur, ValidationStatus

    entrepreneur = db.query(Entrepreneur).filter(Entrepreneur.entrepreneur_id == entrepreneur_id).first()
    if not entrepreneur:
        raise HTTPException(status_code=404, detail="Entrepreneur introuvable")

    entrepreneur.validation_status = ValidationStatus.approved
    entrepreneur.validation_date = datetime.utcnow()
    entrepreneur.validated_by = current_user.user_id

    # Activation de l'utilisateur
    user = get_user_by_id(db, entrepreneur.user_id)
    user.status = UserStatus.active

    db.commit()
    send_entrepreneur_validation_email(user.email, f"{user.first_name} {user.last_name}")

    # Notification
    create_notification(db, NotificationCreate(
        user_id=user.user_id,
        user_type="entrepreneur",
        titre="Compte validé",
        message="Votre compte a été validé avec succès. Bienvenue sur NUKU.",
        type=TypeNotification.success
    ))

    return {"message": "Compte validé avec succès"}

# 🔍 Rejeter une candidature d'entrepreneur
@router.put("/entrepreneurs/{entrepreneur_id}/reject", dependencies=[Depends(require_admin)])
def reject_entrepreneur(entrepreneur_id: UUID, db: Session = Depends(get_db)):
    from app.models.entrepreneur import Entrepreneur, ValidationStatus
    from app.utils.email import send_entrepreneur_rejection_email

    entrepreneur = db.query(Entrepreneur).filter(Entrepreneur.entrepreneur_id == entrepreneur_id).first()
    if not entrepreneur:
        raise HTTPException(status_code=404, detail="Entrepreneur introuvable")

    entrepreneur.validation_status = ValidationStatus.rejected
    db.commit()

    user = get_user_by_id(db, entrepreneur.user_id)
    send_entrepreneur_rejection_email(user.email, f"{user.first_name} {user.last_name}")

    # Notification
    create_notification(db, NotificationCreate(
        user_id=user.user_id,
        user_type="entrepreneur",
        titre="Candidature refusée",
        message="Votre demande d'inscription a été rejetée. Veuillez contacter l'administration pour plus de détails.",
        type=TypeNotification.error
    ))
    
    return {"message": "Candidature rejetée"}

# 🔍 Voir tous les utilisateurs
@router.get("/users", response_model=List[UserResponse], dependencies=[Depends(require_admin)])
def list_all_users(db: Session = Depends(get_db)):
    return db.query(User).all()

# 🔍 Voir tous les experts
@router.get("/experts", response_model=List[ExpertResponse], dependencies=[Depends(require_admin)])
def list_all_experts(db: Session = Depends(get_db)):
    return db.query(Expert).all()

# 🔍 Voir tous les entrepreneurs
@router.get("/entrepreneurs", response_model=List[EntrepreneurResponse], dependencies=[Depends(require_admin)])
def list_all_entrepreneurs(db: Session = Depends(get_db)):
    return db.query(Entrepreneur).all()

# 🔍 Obtenir un entrepreneur par son ID
@router.get("/entrepreneurs/{entrepreneur_id}", response_model=EntrepreneurResponse, dependencies=[Depends(require_admin)])
def get_entrepreneur_by_id_route(
    entrepreneur_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    entrepreneur = get_entrepreneur_by_id(db, entrepreneur_id)
    if not entrepreneur:
        raise HTTPException(status_code=404, detail="Entrepreneur introuvable")
    return entrepreneur

# 🔍 Obtenir un expert par son ID
@router.get("/experts/{expert_id}", response_model=ExpertResponse)
def get_expert_by_id_route(
    expert_id: str,
    db: Session = Depends(get_db),
    current_admin = Depends(require_admin)
):
    expert = get_expert_by_id(db, expert_id)
    if not expert:
        raise HTTPException(status_code=404, detail="Expert introuvable")
    return expert

# supprimer un utilisateur
@router.delete("/users/{user_id}", dependencies=[Depends(require_admin)])
def delete_user(user_id: UUID, db: Session = Depends(get_db)):
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    
    db.delete(user)
    db.commit()
    return {"message": "Utilisateur supprimé avec succès"}

# supprimer un expert
@router.delete("/experts/{expert_id}", dependencies=[Depends(require_admin)])
def delete_expert(expert_id: UUID, db: Session = Depends(get_db)):
    expert = get_expert_by_id(db, expert_id)
    if not expert:
        raise HTTPException(status_code=404, detail="Expert introuvable")
    
    db.delete(expert)
    db.commit()
    return {"message": "Expert supprimé avec succès"}