from sqlalchemy.orm import Session
from app.models.expert import Expert
from app.schemas.expert import ExpertCreate
from app.crud.user import create_user

def create_expert(db: Session, data: ExpertCreate, temp_password: str) -> Expert:
    data.user.password = temp_password
    user = create_user(db, data.user, is_temp_password=True)

    expert = Expert(
        user_id=user.user_id,
        specialization=data.specialization,
        years_of_experience=data.years_of_experience,
        linkedin_profile=data.linkedin_profile,
        cv_url=data.cv_url,
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
