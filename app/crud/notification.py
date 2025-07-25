from sqlalchemy.orm import Session
from app.models.notification import Notification
from app.schemas.notification import NotificationCreate

def create_notification(db: Session, notif: NotificationCreate) -> Notification:
    new_notif = Notification(**notif.dict())
    db.add(new_notif)
    db.commit()
    db.refresh(new_notif)
    return new_notif

def get_notifications_for_user(db: Session, user_id):
    return db.query(Notification).filter(Notification.user_id == user_id).order_by(Notification.date_envoi.desc()).all()

def mark_as_read(db: Session, notif_id):
    notif = db.query(Notification).filter(Notification.id == notif_id).first()
    if notif:
        notif.lu = True
        db.commit()
    return notif

def delete_notification(db: Session, notif_id):
    notif = db.query(Notification).filter(Notification.id == notif_id).first()
    if notif:
        db.delete(notif)
        db.commit()
