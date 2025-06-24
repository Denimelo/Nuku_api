from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from app.crud.expert import create_expert
from app.crud.user import get_user_by_email, get_user_by_id
from app.database import get_db
from app.models.user import UserStatus, UserType
from app.auth.dependencies import get_current_user, require_admin
from app.schemas.expert import ExpertCreate, ExpertResponse
from app.utils.email import send_expert_welcome_email, send_entrepreneur_validation_email, send_entrepreneur_rejection_email
from app.utils.security import generate_temporary_password
from app.schemas.user import UserResponse
from app.schemas.entrepreneur import EntrepreneurResponse
from app.crud.entrepreneur import Entrepreneur
from app.schemas.expert import ExpertResponse
from app.schemas.entrepreneur import EntrepreneurResponse
from app.models.user import User
from app.utils.security import generate_temporary_password
from typing import List
from datetime import datetime
from app.crud.user import create_user
from app.models.expert import Expert
from app.models.entrepreneur import Entrepreneur, ValidationStatus

router = APIRouter(prefix="/admin", tags=["Admin"])

# 🔍 Créer un expert
@router.post("/experts", response_model=ExpertResponse, dependencies=[Depends(require_admin)])
def admin_create_expert(data: ExpertCreate, db: Session = Depends(get_db)):
    if get_user_by_email(db, data.user.email):
        raise HTTPException(status_code=400, detail="Email déjà utilisé")

    temp_password = generate_temporary_password()
    expert = create_expert(db, data, temp_password)
    send_expert_welcome_email(expert.user.email, f"{expert.user.first_name} {expert.user.last_name}", temp_password)
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