from uuid import uuid4
from datetime import datetime, time
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Time
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class UserNotificationPreferences(Base):
    __tablename__ = "user_notification_preferences"

    preference_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, unique=True)
    
    # Préférences générales
    notifications_enabled = Column(Boolean, default=True)
    email_notifications = Column(Boolean, default=True)
    push_notifications = Column(Boolean, default=True)
    sms_notifications = Column(Boolean, default=False)
    
    # Préférences par type de notification (JSON)
    type_preferences = Column(JSON, default=lambda: {
        # Messages
        "message_received": {"in_app": True, "email": True, "push": True},
        "message_reply": {"in_app": True, "email": False, "push": True},
        
        # Appels
        "call_scheduled": {"in_app": True, "email": True, "push": True},
        "call_reminder": {"in_app": True, "email": False, "push": True},
        "call_cancelled": {"in_app": True, "email": True, "push": True},
        
        # Assignments
        "assignment_assigned": {"in_app": True, "email": True, "push": False},
        "assignment_due_soon": {"in_app": True, "email": True, "push": True},
        "assignment_graded": {"in_app": True, "email": True, "push": False},
        
        # Programmes
        "program_accepted": {"in_app": True, "email": True, "push": True},
        "program_started": {"in_app": True, "email": True, "push": False},
        
        # Système
        "system_maintenance": {"in_app": True, "email": True, "push": False},
        "account_security": {"in_app": True, "email": True, "push": True}
    })
    
    # Horaires de réception
    quiet_hours_enabled = Column(Boolean, default=False)
    quiet_hours_start = Column(Time, default=time(22, 0))  # 22h00
    quiet_hours_end = Column(Time, default=time(8, 0))     # 08h00
    
    # Jours de la semaine (0=lundi, 6=dimanche)
    quiet_days = Column(JSON, default=lambda: [])  # [] = pas de jours silencieux
    
    # Fréquence des emails
    email_digest_enabled = Column(Boolean, default=True)
    email_digest_frequency = Column(String(20), default="daily")  # instant, daily, weekly
    email_digest_time = Column(Time, default=time(9, 0))  # 09h00
    
    # Groupement des notifications
    group_similar_notifications = Column(Boolean, default=True)
    max_notifications_per_hour = Column(Integer, default=10)
    
    # Marketing et promotions
    marketing_emails = Column(Boolean, default=False)
    newsletter_subscription = Column(Boolean, default=False)
    
    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    user = relationship("User", back_populates="notification_preferences")

    def __repr__(self):
        return f"<UserNotificationPreferences {self.user_id}>"
    
    def should_send_notification(self, notification_type: str, channel: str) -> bool:
        """Vérifier si une notification doit être envoyée"""
        
        # Vérifications globales
        if not self.notifications_enabled:
            return False
        
        if channel == "email" and not self.email_notifications:
            return False
        
        if channel == "push" and not self.push_notifications:
            return False
        
        if channel == "sms" and not self.sms_notifications:
            return False
        
        # Vérifications par type
        type_prefs = self.type_preferences.get(notification_type, {})
        if not type_prefs.get(channel, False):
            return False
        
        # Vérifier heures silencieuses
        if self.quiet_hours_enabled and channel in ["push", "sms"]:
            now = datetime.now().time()
            if self._is_in_quiet_hours(now):
                return False
        
        return True
    
    def _is_in_quiet_hours(self, current_time: time) -> bool:
        """Vérifier si on est dans les heures silencieuses"""
        start = self.quiet_hours_start
        end = self.quiet_hours_end
        
        if start <= end:
            # Même jour (ex: 22h00 à 23h59)
            return start <= current_time <= end
        else:
            # Chevauchement de jour (ex: 22h00 à 08h00)
            return current_time >= start or current_time <= end