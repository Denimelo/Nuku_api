from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.user import User, UserStatus
from app.utils.security import hash_password
from app.schemas.user import UserCreate

def create_user(db: Session, user_data: UserCreate, is_temp_password=False) -> User:
    hashed_password = hash_password(user_data.password)
    user = User(
        email=user_data.email,
        password_hash=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone=user_data.phone,
        address=user_data.address,
        city=user_data.city,
        country=user_data.country,
        postal_code=user_data.postal_code,
        user_type=user_data.user_type,
        status=UserStatus.pending,
        is_temporary_password=is_temp_password,
        temporary_password_expiration=(datetime.utcnow() + timedelta(hours=6)) if is_temp_password else None
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_email(db: Session, email: str) -> User:
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id) -> User:
    return db.query(User).filter(User.user_id == user_id).first()