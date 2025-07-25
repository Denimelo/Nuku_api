from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from uuid import UUID
import time

from app.database import get_db
from app.auth.dependencies import get_current_user, require_admin
from app.models.user import User
from app.schemas.notification import (
    NotificationCreate, NotificationUpdate, NotificationResponse,
    NotificationSummary, NotificationStats, NotificationFilter,
    NotificationSearchResult, UserNotificationPreferencesUpdate,
    UserNotificationPreferencesResponse, BulkNotificationCreate,
    BulkNotificationResponse, NotificationTemplateCreate,
    NotificationTemplateResponse, NotificationTemplateUpdate
)
from app.crud.notification import (
    create_notification, bulk_create_notifications, get_user_notifications,
    get_notification_by_id, update_notification, mark_notification_as_read,
    mark_all_notifications_as_read, archive_notification, delete_notification,
    search_notifications, get_notification_counts, get_user_notification_preferences,
    update_user_notification_preferences, create_notification_template,
    get_notification_templates, get_notification_stats, cleanup_expired_notifications,
    auto_archive_old_notifications
)

router = APIRouter(prefix="/notifications", tags=["Notifications"])

def format_notification_response(notification) -> dict:
    """Formater réponse de notification"""
    
    return {
        "notification_id": notification.notification_id,
        "user_id": notification.user_id,
        "title": notification.title,
        "message": notification.message,
        "notification_type": notification.notification_type,
        "priority": notification.priority,
        "entity_type": notification.entity_type,
        "entity_id": notification.entity_id,
        "action_url": notification.action_url,
        "action_label": notification.action_label,
        "notification_metadata": notification.notification_metadata,
        "is_actionable": notification.is_actionable,
        "is_read": notification.is_read,
        "is_archived": notification.is_archived,
        "action_taken": notification.action_taken,
        "sent_in_app": notification.sent_in_app,
        "sent_email": notification.sent_email,
        "sent_push": notification.sent_push,
        "sent_sms": notification.sent_sms,
        "created_at": notification.created_at,
        "read_at": notification.read_at,
        "expires_at": notification.expires_at,
        "group_key": notification.group_key,
        "parent_notification_id": notification.parent_notification_id,
        "delivery_attempts": notification.delivery_attempts,
        "delivery_failed": notification.delivery_failed,
        "is_expired": notification.is_expired,
        "age_hours": notification.age_hours
    }

# ========== ROUTES PRINCIPALES ==========

@router.get("/", response_model=List[NotificationResponse])
def get_my_notifications(
    unread_only: bool = Query(False, description="Seulement les non lues"),
    include_archived: bool = Query(False, description="Inclure archivées"),
    limit: int = Query(50, description="Nombre de notifications"),
    skip: int = Query(0, description="Notifications à ignorer"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """📋 Mes notifications"""
    
    notifications = get_user_notifications(
        db, current_user.user_id, unread_only, include_archived, limit, skip
    )
    
    return [
        NotificationResponse(**format_notification_response(notification))
        for notification in notifications
    ]

@router.get("/summary", response_model=NotificationSummary)
def get_notifications_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """📊 Résumé de mes notifications"""
    
    # Comptes
    counts = get_notification_counts(db, current_user.user_id)
    
    # Notifications récentes
    recent = get_user_notifications(db, current_user.user_id, limit=5)
    recent_formatted = [
        NotificationResponse(**format_notification_response(n))
        for n in recent
    ]
    
    return NotificationSummary(
        total_notifications=counts["total"],
        unread_count=counts["unread"],
        urgent_count=counts["urgent"],
        actionable_count=counts["actionable"],
        recent_notifications=recent_formatted
    )

@router.get("/counts")
def get_notification_counts_route(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """🔢 Compteurs de notifications"""
    
    return get_notification_counts(db, current_user.user_id)

@router.get("/{notification_id}", response_model=NotificationResponse)
def get_notification_details(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """📖 Détails d'une notification"""
    
    notification = get_notification_by_id(db, notification_id, current_user.user_id)
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification non trouvée"
        )
    
    return NotificationResponse(**format_notification_response(notification))

@router.put("/{notification_id}", response_model=NotificationResponse)
def update_notification_route(
    notification_id: UUID,
    update_data: NotificationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """✏️ Mettre à jour notification"""
    
    notification = update_notification(db, notification_id, update_data, current_user.user_id)
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification non trouvée"
        )
    
    return NotificationResponse(**format_notification_response(notification))

@router.post("/{notification_id}/read")
def mark_notification_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """✅ Marquer comme lue"""
    
    success = mark_notification_as_read(db, notification_id, current_user.user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification non trouvée"
        )
    
    return {"message": "Notification marquée comme lue"}

@router.post("/read-all")
def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """✅ Marquer toutes comme lues"""
    
    count = mark_all_notifications_as_read(db, current_user.user_id)
    
    return {"message": f"{count} notifications marquées comme lues"}

@router.post("/{notification_id}/archive")
def archive_notification_route(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """📦 Archiver notification"""
    
    success = archive_notification(db, notification_id, current_user.user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification non trouvée"
        )
    
    return {"message": "Notification archivée"}

@router.delete("/{notification_id}")
def delete_notification_route(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """🗑️ Supprimer notification"""
    
    success = delete_notification(db, notification_id, current_user.user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification non trouvée"
        )
    
    return {"message": "Notification supprimée"}

# ========== RECHERCHE ==========

@router.post("/search", response_model=NotificationSearchResult)
def search_notifications_route(
    filters: NotificationFilter,
    skip: int = Query(0),
    limit: int = Query(20),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """🔍 Rechercher notifications"""
    
    start_time = time.time()
    
    notifications, total_count = search_notifications(
        db, current_user.user_id, filters, skip, limit
    )
    
    search_time_ms = (time.time() - start_time) * 1000
    
    return NotificationSearchResult(
        notifications=[
            NotificationResponse(**format_notification_response(n))
            for n in notifications
        ],
        total_count=total_count,
        search_time_ms=round(search_time_ms, 2)
    )

# ========== PRÉFÉRENCES ==========

@router.get("/preferences", response_model=UserNotificationPreferencesResponse)
def get_my_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """⚙️ Mes préférences de notifications"""
    
    preferences = get_user_notification_preferences(db, current_user.user_id)
    
    return UserNotificationPreferencesResponse(
        preference_id=preferences.preference_id,
        user_id=preferences.user_id,
        notifications_enabled=preferences.notifications_enabled,
        email_notifications=preferences.email_notifications,
        push_notifications=preferences.push_notifications,
        sms_notifications=preferences.sms_notifications,
        type_preferences=preferences.type_preferences,
        quiet_hours_enabled=preferences.quiet_hours_enabled,
        quiet_hours_start=preferences.quiet_hours_start,
        quiet_hours_end=preferences.quiet_hours_end,
        quiet_days=preferences.quiet_days,
        email_digest_enabled=preferences.email_digest_enabled,
        email_digest_frequency=preferences.email_digest_frequency,
        email_digest_time=preferences.email_digest_time,
        group_similar_notifications=preferences.group_similar_notifications,
        max_notifications_per_hour=preferences.max_notifications_per_hour,
        marketing_emails=preferences.marketing_emails,
        newsletter_subscription=preferences.newsletter_subscription,
        created_at=preferences.created_at,
        updated_at=preferences.updated_at
    )

@router.put("/preferences", response_model=UserNotificationPreferencesResponse)
def update_my_notification_preferences(
    update_data: UserNotificationPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """⚙️ Modifier mes préférences"""
    
    preferences = update_user_notification_preferences(
        db, current_user.user_id, update_data
    )
    
    return UserNotificationPreferencesResponse(
        preference_id=preferences.preference_id,
        user_id=preferences.user_id,
        notifications_enabled=preferences.notifications_enabled,
        email_notifications=preferences.email_notifications,
        push_notifications=preferences.push_notifications,
        sms_notifications=preferences.sms_notifications,
        type_preferences=preferences.type_preferences,
        quiet_hours_enabled=preferences.quiet_hours_enabled,
        quiet_hours_start=preferences.quiet_hours_start,
        quiet_hours_end=preferences.quiet_hours_end,
        quiet_days=preferences.quiet_days,
        email_digest_enabled=preferences.email_digest_enabled,
        email_digest_frequency=preferences.email_digest_frequency,
        email_digest_time=preferences.email_digest_time,
        group_similar_notifications=preferences.group_similar_notifications,
        max_notifications_per_hour=preferences.max_notifications_per_hour,
        marketing_emails=preferences.marketing_emails,
        newsletter_subscription=preferences.newsletter_subscription,
        created_at=preferences.created_at,
        updated_at=preferences.updated_at
    )

# ========== STATISTIQUES ==========

@router.get("/stats", response_model=NotificationStats)
def get_my_notification_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """📊 Mes statistiques de notifications"""
    
    stats = get_notification_stats(db, current_user.user_id)
    return NotificationStats(**stats)

# ========== ADMINISTRATION (ADMIN SEULEMENT) ==========

@router.post("/bulk", response_model=BulkNotificationResponse)
def send_bulk_notifications(
   bulk_data: BulkNotificationCreate,
   background_tasks: BackgroundTasks,
   current_user: User = Depends(require_admin),
   db: Session = Depends(get_db)
):
   """📢 Envoyer notifications en masse (Admin)"""
   
   # Traiter en arrière-plan pour les gros volumes
   if len(bulk_data.user_ids) > 100:
       background_tasks.add_task(
           _process_bulk_notifications_async,
           db, bulk_data
       )
       return BulkNotificationResponse(
           sent_count=0,
           failed_count=0,
           failed_users=[],
           message="Notifications en cours de traitement en arrière-plan"
       )
   
   # Traitement immédiat pour petits volumes
   sent_count, failed_count, failed_users = bulk_create_notifications(db, bulk_data)
   
   return BulkNotificationResponse(
       sent_count=sent_count,
       failed_count=failed_count,
       failed_users=failed_users
   )

@router.post("/templates", response_model=NotificationTemplateResponse)
def create_notification_template_route(
   template_data: NotificationTemplateCreate,
   current_user: User = Depends(require_admin),
   db: Session = Depends(get_db)
):
   """📝 Créer template de notification (Admin)"""
   
   template = create_notification_template(
       db, 
       template_data.dict(),
       current_user.user_id
   )
   
   return NotificationTemplateResponse(
       template_id=template.template_id,
       name=template.name,
       notification_type=template.notification_type,
       description=template.description,
       title_template=template.title_template,
       message_template=template.message_template,
       email_subject_template=template.email_subject_template,
       email_body_template=template.email_body_template,
       push_title_template=template.push_title_template,
       push_body_template=template.push_body_template,
       priority=template.priority,
       default_channels=template.default_channels,
       action_url_template=template.action_url_template,
       action_label=template.action_label,
       conditions=template.conditions,
       user_preferences_key=template.user_preferences_key,
       is_active=template.is_active,
       is_system=template.is_system,
       created_by=template.created_by,
       created_at=template.created_at,
       updated_at=template.updated_at,
       usage_count=template.usage_count,
       last_used_at=template.last_used_at
   )

@router.get("/templates", response_model=List[NotificationTemplateResponse])
def get_notification_templates_route(
   notification_type: Optional[str] = Query(None),
   active_only: bool = Query(True),
   current_user: User = Depends(require_admin),
   db: Session = Depends(get_db)
):
   """📋 Liste des templates (Admin)"""
   
   templates = get_notification_templates(db, notification_type, active_only)
   
   return [
       NotificationTemplateResponse(
           template_id=template.template_id,
           name=template.name,
           notification_type=template.notification_type,
           description=template.description,
           title_template=template.title_template,
           message_template=template.message_template,
           email_subject_template=template.email_subject_template,
           email_body_template=template.email_body_template,
           push_title_template=template.push_title_template,
           push_body_template=template.push_body_template,
           priority=template.priority,
           default_channels=template.default_channels,
           action_url_template=template.action_url_template,
           action_label=template.action_label,
           conditions=template.conditions,
           user_preferences_key=template.user_preferences_key,
           is_active=template.is_active,
           is_system=template.is_system,
           created_by=template.created_by,
           created_at=template.created_at,
           updated_at=template.updated_at,
           usage_count=template.usage_count,
           last_used_at=template.last_used_at
       ) for template in templates
   ]

@router.post("/cleanup")
def cleanup_notifications(
   current_user: User = Depends(require_admin),
   db: Session = Depends(get_db)
):
   """🧹 Nettoyer notifications expirées (Admin)"""
   
   expired_count = cleanup_expired_notifications(db)
   archived_count = auto_archive_old_notifications(db)
   
   return {
       "message": "Nettoyage terminé",
       "expired_deleted": expired_count,
       "auto_archived": archived_count
   }

# ========== UTILITAIRES ==========

@router.get("/types")
def get_notification_types():
   """📋 Types de notifications disponibles"""
   from app.models.notification import NotificationType
   
   return {
       "notification_types": [
           {
               "value": type.value,
               "label": _get_type_label(type.value),
               "description": _get_type_description(type.value),
               "category": _get_type_category(type.value)
           } for type in NotificationType
       ]
   }

@router.get("/channels")
def get_notification_channels():
   """📡 Canaux de notification disponibles"""
   from app.schemas.notification import NotificationChannel
   
   return {
       "channels": [
           {
               "value": channel.value,
               "label": _get_channel_label(channel.value),
               "description": _get_channel_description(channel.value)
           } for channel in NotificationChannel
       ]
   }

# ========== HELPERS ==========

def _process_bulk_notifications_async(db: Session, bulk_data: BulkNotificationCreate):
   """Traiter notifications en masse de façon asynchrone"""
   try:
       sent_count, failed_count, failed_users = bulk_create_notifications(db, bulk_data)
       # TODO: Notifier admin du résultat
       print(f"Bulk notifications: {sent_count} sent, {failed_count} failed")
   except Exception as e:
       print(f"Erreur bulk notifications: {e}")

def _get_type_label(notification_type: str) -> str:
   """Labels des types de notifications"""
   labels = {
       "message_received": "Message reçu",
       "message_reply": "Réponse à message",
       "message_mention": "Mention dans message",
       "program_accepted": "Programme accepté",
       "program_rejected": "Programme rejeté",
       "program_started": "Programme commencé",
       "program_completed": "Programme terminé",
       "module_assigned": "Module assigné",
       "module_completed": "Module complété",
       "assignment_assigned": "Devoir assigné",
       "assignment_due_soon": "Échéance de devoir",
       "assignment_graded": "Devoir noté",
       "assignment_overdue": "Devoir en retard",
       "call_scheduled": "Appel programmé",
       "call_reminder": "Rappel d'appel",
       "call_cancelled": "Appel annulé",
       "call_started": "Appel commencé",
       "call_missed": "Appel manqué",
       "expert_application": "Candidature expert",
       "expert_approved": "Expert approuvé",
       "expert_assigned": "Expert assigné",
       "entrepreneur_application": "Candidature entrepreneur",
       "entrepreneur_profile_incomplete": "Profil incomplet",
       "system_maintenance": "Maintenance système",
       "system_update": "Mise à jour système",
       "account_security": "Sécurité du compte",
       "payment_reminder": "Rappel de paiement",
       "follow_request": "Demande de suivi",
       "new_follower": "Nouveau follower",
       "achievement_unlocked": "Achievement débloqué"
   }
   return labels.get(notification_type, notification_type.title())

def _get_type_description(notification_type: str) -> str:
   """Descriptions des types"""
   descriptions = {
       "message_received": "Notification lors de la réception d'un nouveau message",
       "call_reminder": "Rappel avant le début d'un appel programmé",
       "assignment_due_soon": "Notification d'échéance proche pour un devoir",
       "program_accepted": "Confirmation d'acceptation dans un programme",
       # Ajouter autres descriptions...
   }
   return descriptions.get(notification_type, "Notification du système")

def _get_type_category(notification_type: str) -> str:
   """Catégories des types"""
   categories = {
       "message_received": "Messages",
       "message_reply": "Messages",
       "message_mention": "Messages",
       "program_accepted": "Programmes",
       "program_rejected": "Programmes",
       "program_started": "Programmes",
       "program_completed": "Programmes",
       "module_assigned": "Formation",
       "module_completed": "Formation",
       "assignment_assigned": "Formation",
       "assignment_due_soon": "Formation",
       "assignment_graded": "Formation",
       "assignment_overdue": "Formation",
       "call_scheduled": "Appels",
       "call_reminder": "Appels",
       "call_cancelled": "Appels",
       "call_started": "Appels",
       "call_missed": "Appels",
       "expert_application": "Experts",
       "expert_approved": "Experts",
       "expert_assigned": "Experts",
       "entrepreneur_application": "Entrepreneurs",
       "entrepreneur_profile_incomplete": "Entrepreneurs",
       "system_maintenance": "Système",
       "system_update": "Système",
       "account_security": "Sécurité",
       "payment_reminder": "Paiements",
       "follow_request": "Social",
       "new_follower": "Social",
       "achievement_unlocked": "Gamification"
   }
   return categories.get(notification_type, "Autre")

def _get_channel_label(channel: str) -> str:
   """Labels des canaux"""
   labels = {
       "in_app": "Dans l'application",
       "email": "Email",
       "push": "Notification push",
       "sms": "SMS"
   }
   return labels.get(channel, channel.title())

def _get_channel_description(channel: str) -> str:
   """Descriptions des canaux"""
   descriptions = {
       "in_app": "Notification visible dans l'interface de l'application",
       "email": "Notification envoyée par email",
       "push": "Notification push sur mobile/desktop",
       "sms": "Notification par SMS (pour urgences)"
   }
   return descriptions.get(channel, "Canal de notification")