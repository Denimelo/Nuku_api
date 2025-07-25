from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta
from app.crud.notification import (
    create_notification_from_template, create_message_notification,
    create_call_reminder_notification, create_assignment_due_notification,
    create_notification
)
from app.schemas.notification import NotificationCreate, NotificationChannel, NotificationType, NotificationPriority

class NotificationService:
    """Service centralisé pour les notifications"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ========== NOTIFICATIONS DE MESSAGES ==========
    
    def notify_message_received(
        self, 
        recipient_id: UUID, 
        sender_name: str, 
        message_preview: str, 
        message_id: UUID
    ):
        """Notifier réception de message"""
        return create_message_notification(
            self.db, recipient_id, sender_name, message_preview, message_id
        )
    
    def notify_message_reply(
        self, 
        recipient_id: UUID, 
        sender_name: str, 
        original_subject: str,
        message_id: UUID
    ):
        """Notifier réponse à message"""
        notification_data = NotificationCreate(
            user_id=recipient_id,
            title=f"Réponse de {sender_name}",
            message=f"Réponse à: {original_subject}",
            notification_type=NotificationType.message_reply,
            entity_type="message",
            entity_id=message_id,
            action_url=f"/messages/{message_id}",
            action_label="Voir la réponse",
            channels=[NotificationChannel.in_app, NotificationChannel.push]
        )
        return create_notification(self.db, notification_data)
    
    # ========== NOTIFICATIONS D'APPELS ==========
    
    def notify_call_scheduled(
        self, 
        participant_id: UUID, 
        call_title: str, 
        call_start: datetime,
        call_id: UUID
    ):
        """Notifier programmation d'appel"""
        notification_data = NotificationCreate(
            user_id=participant_id,
            title="Nouvel appel programmé",
            message=f"Appel '{call_title}' prévu le {call_start.strftime('%d/%m/%Y à %H:%M')}",
            notification_type=NotificationType.call_scheduled,
            entity_type="call",
            entity_id=call_id,
            action_url=f"/calls/{call_id}",
            action_label="Voir les détails",
            channels=[NotificationChannel.in_app, NotificationChannel.email]
        )
        return create_notification(self.db, notification_data)
    
    def notify_call_reminder(
        self, 
        participant_id: UUID, 
        call_title: str, 
        call_id: UUID,
        minutes_before: int = 15
    ):
        """Envoyer rappel d'appel"""
        return create_call_reminder_notification(
            self.db, participant_id, call_title, call_id, minutes_before
        )
    
    def notify_call_cancelled(
        self, 
        participant_id: UUID, 
        call_title: str, 
        reason: str,
        call_id: UUID
    ):
        """Notifier annulation d'appel"""
        notification_data = NotificationCreate(
            user_id=participant_id,
            title="Appel annulé",
            message=f"L'appel '{call_title}' a été annulé. Raison: {reason}",
            notification_type=NotificationType.call_cancelled,
            priority=NotificationPriority.high,
            entity_type="call",
            entity_id=call_id,
            channels=[NotificationChannel.in_app, NotificationChannel.email, NotificationChannel.push]
        )
        return create_notification(self.db, notification_data)
    
    # ========== NOTIFICATIONS DE FORMATION ==========
    
    def notify_assignment_assigned(
        self, 
        student_id: UUID, 
        assignment_title: str, 
        due_date: datetime,
        assignment_id: UUID
    ):
        """Notifier nouveau devoir"""
        due_str = due_date.strftime('%d/%m/%Y à %H:%M') if due_date else "Sans échéance"
        
        notification_data = NotificationCreate(
            user_id=student_id,
            title="Nouveau devoir assigné",
            message=f"Devoir '{assignment_title}' - Échéance: {due_str}",
            notification_type=NotificationType.assignment_assigned,
            entity_type="assignment",
            entity_id=assignment_id,
            action_url=f"/assignments/{assignment_id}",
            action_label="Voir le devoir",
            channels=[NotificationChannel.in_app, NotificationChannel.email]
        )
        return create_notification(self.db, notification_data)
    
    def notify_assignment_graded(
        self, 
        student_id: UUID, 
        assignment_title: str, 
        score: float,
        assignment_id: UUID
    ):
        """Notifier notation de devoir"""
        notification_data = NotificationCreate(
            user_id=student_id,
            title="Devoir noté",
            message=f"Votre devoir '{assignment_title}' a été noté: {score}/100",
            notification_type=NotificationType.assignment_graded,
            entity_type="assignment",
            entity_id=assignment_id,
            action_url=f"/assignments/{assignment_id}",
            action_label="Voir la note",
            channels=[NotificationChannel.in_app, NotificationChannel.email]
        )
        return create_notification(self.db, notification_data)
    
    def notify_assignment_due_soon(
        self, 
        student_id: UUID, 
        assignment_title: str, 
        assignment_id: UUID,
        due_date: datetime
    ):
        """Notifier échéance proche de devoir"""
        return create_assignment_due_notification(
            self.db, student_id, assignment_title, assignment_id, due_date
        )
    
    # ========== NOTIFICATIONS DE PROGRAMMES ==========
    
    def notify_program_accepted(
        self, 
        entrepreneur_id: UUID, 
        program_name: str,
        program_id: UUID
    ):
        """Notifier acceptation dans programme"""
        notification_data = NotificationCreate(
            user_id=entrepreneur_id,
            title="Candidature acceptée !",
            message=f"Félicitations ! Vous avez été accepté dans le programme '{program_name}'",
            notification_type=NotificationType.program_accepted,
            priority=NotificationPriority.high,
            entity_type="program",
            entity_id=program_id,
            action_url=f"/programs/{program_id}",
            action_label="Voir le programme",
            channels=[NotificationChannel.in_app, NotificationChannel.email, NotificationChannel.push]
        )
        return create_notification(self.db, notification_data)
    
    def notify_program_started(
        self, 
        entrepreneur_id: UUID, 
        program_name: str,
        program_id: UUID
    ):
        """Notifier début de programme"""
        notification_data = NotificationCreate(
            user_id=entrepreneur_id,
            title="Programme commencé",
            message=f"Le programme '{program_name}' a officiellement commencé !",
            notification_type=NotificationType.program_started,
            entity_type="program",
            entity_id=program_id,
            action_url=f"/programs/{program_id}",
            action_label="Accéder au programme",
            channels=[NotificationChannel.in_app, NotificationChannel.email]
        )
        return create_notification(self.db, notification_data)
    
    # ========== NOTIFICATIONS SYSTÈME ==========
    
    def notify_system_maintenance(
        self, 
        user_ids: List[UUID], 
        start_time: datetime, 
        duration_hours: int
    ):
        """Notifier maintenance système"""
        start_str = start_time.strftime('%d/%m/%Y à %H:%M')
        
        for user_id in user_ids:
            notification_data = NotificationCreate(
                user_id=user_id,
                title="Maintenance programmée",
                message=f"Maintenance du système prévue le {start_str} (durée: {duration_hours}h)",
                notification_type=NotificationType.system_maintenance,
                priority=NotificationPriority.high,
                expires_at=start_time + timedelta(hours=duration_hours),
                channels=[NotificationChannel.in_app, NotificationChannel.email]
            )
            create_notification(self.db, notification_data)
    
    def notify_account_security(
        self, 
        user_id: UUID, 
        security_event: str, 
        ip_address: str
    ):
        """Notifier événement de sécurité"""
        notification_data = NotificationCreate(
            user_id=user_id,
            title="Alerte sécurité",
            message=f"Événement de sécurité détecté: {security_event} depuis {ip_address}",
            notification_type=NotificationType.account_security,
            priority=NotificationPriority.urgent,
            is_actionable=True,
            action_url="/settings/security",
            action_label="Vérifier la sécurité",
            channels=[NotificationChannel.in_app, NotificationChannel.email, NotificationChannel.push]
        )
        return create_notification(self.db, notification_data)
    
    # ========== NOTIFICATIONS SOCIALES ==========
    
    def notify_new_follower(
        self, 
        user_id: UUID, 
        follower_name: str,
        follower_id: UUID
    ):
        """Notifier nouveau follower"""
        notification_data = NotificationCreate(
            user_id=user_id,
            title="Nouveau follower",
            message=f"{follower_name} vous suit maintenant",
            notification_type=NotificationType.new_follower,
            entity_type="user",
            entity_id=follower_id,
            action_url=f"/users/{follower_id}",
            action_label="Voir le profil",
            channels=[NotificationChannel.in_app, NotificationChannel.push]
        )
        return create_notification(self.db, notification_data)
    
    def notify_achievement_unlocked(
        self, 
        user_id: UUID, 
        achievement_name: str, 
        achievement_description: str
    ):
        """Notifier déblocage d'achievement"""
        notification_data = NotificationCreate(
            user_id=user_id,
            title="Achievement débloqué !",
            message=f"Vous avez débloqué: {achievement_name} - {achievement_description}",
            notification_type=NotificationType.achievement_unlocked,
            priority=NotificationPriority.low,
            action_url="/profile/achievements",
            action_label="Voir mes achievements",
            channels=[NotificationChannel.in_app, NotificationChannel.push]
        )
        return create_notification(self.db, notification_data)

# ========== FACTORY FUNCTION ==========

def get_notification_service(db: Session) -> NotificationService:
    """Factory pour créer service de notifications"""
    return NotificationService(db)
