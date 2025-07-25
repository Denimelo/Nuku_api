from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.notification import NotificationCreate, NotificationRead, NotificationUpdate
from app.crud.notification import create_notification, get_notifications_for_user, mark_as_read, delete_notification
from uuid import UUID

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.post("/", response_model=NotificationRead)
def send_notification(payload: NotificationCreate, db: Session = Depends(get_db)):
    return create_notification(db, payload)

@router.get("/user/{user_id}", response_model=list[NotificationRead])
def list_user_notifications(user_id: UUID, db: Session = Depends(get_db)):
    return get_notifications_for_user(db, user_id)

@router.patch("/{notif_id}", response_model=NotificationRead)
def mark_notification_read(notif_id: UUID, db: Session = Depends(get_db)):
    notif = mark_as_read(db, notif_id)
    if not notif:
        raise HTTPException(status_code=404, detail="Notification non trouvée")
    return notif

@router.delete("/{notif_id}")
def remove_notification(notif_id: UUID, db: Session = Depends(get_db)):
    delete_notification(db, notif_id)
    return {"message": "Notification supprimée"}
