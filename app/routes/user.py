from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.crud.user import get_user_by_id
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/user", tags=["User"])

@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user = Depends(get_current_user)):
    return current_user