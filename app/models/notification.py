from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy import Column, String, Text, Boolean, ForeignKey, DateTime, Enum, Integer
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class NotificationType(str, enum.Enum):
    # Messages
    message_received = "message_received"
    message_reply = "message_reply"
    message_mention = "message_mention"
    
    # Programmes
    program_accepted = "program_accepted"
    program_rejected = "program_rejected"
    program_started = "program_started"
    program_completed = "program_completed"
    
    # Modules et assignments
    module_assigned = "module_assigned"
    module_completed = "module_completed"
    assignment_assigned = "assignment_assigned"
    assignment_due_soon = "assignment_due_soon"
    assignment_graded = "assignment_graded"
    assignment_overdue = "assignment_overdue"
    
    # Appels
    call_scheduled = "call_scheduled"
    call_reminder = "call_reminder"
    call_cancelled = "call_cancelled"
    call_started = "call_started"
    call_missed = "call_missed"
    
    # Experts
    expert_application = "expert_application"
    expert_approved = "expert_approved"
    expert_assigned = "expert_assigned"
    
    # Entrepreneurs
    entrepreneur_application = "entrepreneur_application"
    entrepreneur_profile_incomplete = "entrepreneur_profile_incomplete"
    
    # Système
    system_maintenance = "system_maintenance"
    system_update = "system_update"
    account_security = "account_security"
    payment_reminder = "payment_reminder"
    
    # Activité sociale
    follow_request = "follow_request"
    new_follower = "new_follower"
    achievement_unlocked = "achievement_unlocked"

class NotificationPriority(str, enum.Enum):
    low = "low"           # Informatif
    normal = "normal"     # Standard
    high = "high"         # Important
    urgent = "urgent"     # Critique

class NotificationChannel(str, enum.Enum):
    in_app = "in_app"         # Notification dans l'app
    email = "email"           # Email
    push = "push"             # Notification push
    sms = "sms"               # SMS
    slack = "slack"           # Slack (pour équipe interne)

class Notification(Base):
    __tablename__ = "notifications"

    notification_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Destinataire
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    
    # Contenu
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(Enum(NotificationType), nullable=False)
    priority = Column(Enum(NotificationPriority), default=NotificationPriority.normal)
    
    # Métadonnées contextuelles
    entity_type = Column(String(50), nullable=True)    # "call", "assignment", "message", etc.
    entity_id = Column(UUID(as_uuid=True), nullable=True)  # ID de l'entité liée
    action_url = Column(String(500), nullable=True)    # URL d'action
    action_label = Column(String(100), nullable=True)  # Label du bouton d'action
    
    # Données supplémentaires
    notification_metadata = Column(JSON, nullable=True)  # Données contextuelles supplémentaires
    
    # États
    is_read = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)
    is_actionable = Column(Boolean, default=False)    # Nécessite une action
    action_taken = Column(Boolean, default=False)     # Action effectuée
    
    # Canaux de diffusion
    sent_in_app = Column(Boolean, default=True)
    sent_email = Column(Boolean, default=False)
    sent_push = Column(Boolean, default=False)
    sent_sms = Column(Boolean, default=False)
    
    # Temporalité
    created_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)      # Expiration automatique
    
    # Groupement
    group_key = Column(String(100), nullable=True)    # Pour regrouper notifications similaires
    parent_notification_id = Column(UUID(as_uuid=True), ForeignKey("notifications.notification_id"), nullable=True)
    
    # Retry et delivery
    delivery_attempts = Column(Integer, default=0)
    last_delivery_attempt = Column(DateTime, nullable=True)
    delivery_failed = Column(Boolean, default=False)
    failure_reason = Column(Text, nullable=True)
    
    # Relations
    user = relationship("User", back_populates="notifications")
    parent_notification = relationship("Notification", remote_side=[notification_id])
    child_notifications = relationship("Notification", back_populates="parent_notification")

    def __repr__(self):
        return f"<Notification {self.title} -> {self.user_id}>"
    
    @property
    def is_expired(self) -> bool:
        """Vérifier si la notification a expiré"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def age_hours(self) -> float:
        """Âge en heures"""
        return (datetime.utcnow() - self.created_at).total_seconds() / 3600
    
    @property
    def should_auto_archive(self) -> bool:
        """Devrait être archivée automatiquement"""
        # Archiver après 30 jours si lue ou 7 jours si non lue
        if self.is_read:
            return self.age_hours > (30 * 24)
        else:
            return self.age_hours > (7 * 24)