from app.models.user import UserStatus
from app.schemas.user import UserType
from app.utils.url_to_str import optional_str
from sqlalchemy.orm import Session
from app.models.expert import Expert
from app.schemas.expert import ExpertCreate
from app.crud.user import create_user

def create_expert(db: Session, data: ExpertCreate, temp_password: str):
    from app.models.user import User
    from app.models.expert import Expert
    from app.utils.security import hash_password
    from uuid import uuid4

    # Crée un nouvel utilisateur
    user = User(
        user_id=uuid4(),
        first_name=data.user.first_name,
        last_name=data.user.last_name,
        email=data.user.email,
        phone=data.user.phone,
        password_hash=hash_password(temp_password),
        user_type=UserType.expert,
        status=UserStatus.active,
    )
    db.add(user)
    db.flush()  # pour avoir l'user_id

    # Crée l'expert lié
    expert = Expert(
        expert_id=uuid4(),
        user_id=user.user_id,
        specialization=data.specialization,
        years_of_experience=data.years_of_experience,
        linkedin_profile=optional_str(data.linkedin_profile),
        cv_url=optional_str(data.cv_url),
        bio=data.bio,
        hourly_rate=data.hourly_rate,
        is_active=data.is_active
    )
    db.add(expert)
    db.commit()
    db.refresh(expert)
    return expert



def get_expert_by_user_id(db: Session, user_id) -> Expert:
    return db.query(Expert).filter(Expert.user_id == user_id).first()
