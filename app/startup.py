from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.user import User, UserType, UserStatus
from app.utils.security import hash_password
from uuid import uuid4
import os
from dotenv import load_dotenv
load_dotenv()


def create_default_admin():
    db: Session = SessionLocal()
    admin_email = os.getenv("DEFAULT_ADMIN_EMAIL", "lumiereakn@gmail.com")
    existing_admin = db.query(User).filter(User.email == admin_email).first()

    if not existing_admin:
        admin_user = User(
            user_id=uuid4(),
            email=admin_email,
            password_hash=hash_password(os.getenv("DEFAULT_ADMIN_PASSWORD")),
            first_name="Narcisse",
            last_name="NUKU",
            user_type=UserType.admin,
            status=UserStatus.active
        )
        db.add(admin_user)
        db.commit()
        print("✅ Administrateur par défaut créé.")
    else:
        print("ℹ️ Administrateur déjà existant.")
    db.close()
