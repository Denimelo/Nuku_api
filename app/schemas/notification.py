from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

class TypeNotification(str, Enum):
    info = "info"
    warning = "warning"
    error = "error"
    success = "success"

class NotificationBase(BaseModel):
    user_id: UUID
    user_type: str
    titre: str
    message: str
    type: TypeNotification = TypeNotification.info

class NotificationCreate(NotificationBase):
    pass

class NotificationUpdate(BaseModel):
    lu: bool

class NotificationRead(NotificationBase):
    id: UUID
    lu: bool
    date_envoi: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "d1f4c1c1-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                "user_id": "abf4c1c1-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                "user_type": "client",
                "titre": "Nouvelle commande",
                "message": "Votre commande a été validée.",
                "type": "success",
                "lu": False,
                "date_envoi": datetime.utcnow().isoformat()
            }
        }