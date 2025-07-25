from uuid import uuid4
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.notification import NotificationType, NotificationPriority, NotificationChannel

class NotificationTemplate(Base):
    __tablename__ = "notification_templates"

    template_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Identification
    name = Column(String(100), nullable=False)
    notification_type = Column(Enum(NotificationType), nullable=False)
    description = Column(Text, nullable=True)
    
    # Templates de contenu
    title_template = Column(String(255), nullable=False)     # "Nouveau message de {sender_name}"
    message_template = Column(Text, nullable=False)          # "Vous avez reçu un message: {message_preview}"
    email_subject_template = Column(String(255), nullable=True)
    email_body_template = Column(Text, nullable=True)
    push_title_template = Column(String(100), nullable=True)
    push_body_template = Column(String(255), nullable=True)
    
    # Configuration
    priority = Column(Enum(NotificationPriority), default=NotificationPriority.normal)
    default_channels = Column(JSON, nullable=True)  # ["in_app", "email"]
    
    # Actions
    action_url_template = Column(String(500), nullable=True)  # "/messages/{message_id}"
    action_label = Column(String(100), nullable=True)        # "Voir le message"
    
    # Conditions et règles
    conditions = Column(JSON, nullable=True)  # Conditions pour déclencher
    user_preferences_key = Column(String(100), nullable=True)  # Clé dans préférences utilisateur
    
    # États
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)  # Template système (non modifiable)
    
    # Métadonnées
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Usage
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime, nullable=True)
    
    # Relations
    created_by_user = relationship("User")

    def __repr__(self):
        return f"<NotificationTemplate {self.name}>"
    
    def render_content(self, context: dict) -> dict:
        """Rendre le contenu avec le contexte fourni"""
        try:
            title = self.title_template.format(**context)
            message = self.message_template.format(**context)
            
            result = {
                "title": title,
                "message": message,
                "action_label": self.action_label
            }
            
            if self.action_url_template:
                result["action_url"] = self.action_url_template.format(**context)
            
            if self.email_subject_template:
                result["email_subject"] = self.email_subject_template.format(**context)
            
            if self.email_body_template:
                result["email_body"] = self.email_body_template.format(**context)
            
            if self.push_title_template:
                result["push_title"] = self.push_title_template.format(**context)
            
            if self.push_body_template:
                result["push_body"] = self.push_body_template.format(**context)
            
            return result
            
        except KeyError as e:
            raise ValueError(f"Contexte manquant pour le template: {e}")