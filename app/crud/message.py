from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from ..models.message import Message
from ..schemas.message import MessageCreate

def create_message(db: Session, msg_in: MessageCreate):
    msg = Message(
        sender_id=msg_in.sender_id,
        receiver_id=msg_in.receiver_id,
        program_id=msg_in.program_id,
        message_text=msg_in.message_text,
        sent_at=datetime.utcnow(),
        read_status=False
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg

def get_messages_for_user(db: Session, user_id: UUID):
    return db.query(Message).filter(
        (Message.sender_id == user_id) | (Message.receiver_id == user_id)
    ).order_by(Message.sent_at.desc()).all()

def mark_message_as_read(db: Session, message_id: UUID):
    msg = db.query(Message).filter(Message.message_id == message_id).first()
    if msg:
        msg.read_status = True
        db.commit()
        db.refresh(msg)
    return msg

def delete_message(db: Session, message_id: UUID):
    msg = db.query(Message).filter(Message.message_id == message_id).first()
    if not msg:
        return None
    db.delete(msg)
    db.commit()
    return msg