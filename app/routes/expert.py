from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import UserType
from app.crud.expert import get_expert_by_user_id
from app.auth.dependencies import get_current_user
from app.schemas.expert import ExpertResponse

router = APIRouter(prefix="/expert", tags=["Expert"])

# 🔍 Obtenir le profil expert de l'utilisateur connecté
@router.get("/me", response_model=ExpertResponse)
def get_my_expert_profile(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if current_user.user_type != UserType.expert:
        raise HTTPException(status_code=403, detail="Accès réservé aux experts")

    expert = get_expert_by_user_id(db, current_user.user_id)
    if not expert:
        raise HTTPException(status_code=404, detail="Profil expert non trouvé")

    return expert
