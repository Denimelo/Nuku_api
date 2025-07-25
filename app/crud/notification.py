from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, asc, func
from uuid import UUID
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from app.models.notification import Notification, NotificationChannel, NotificationType, NotificationPriority
from app.models.notificationTemplate import NotificationTemplate
from app.models.userNotificationPreferences import UserNotificationPreferences
from app.models.user import User
from app.schemas.notification import (
    NotificationCreate, NotificationUpdate, NotificationFilter,
    UserNotificationPreferencesUpdate, BulkNotificationCreate
)

# ========== CRUD NOTIFICATION ==========

def create_notification(
    db: Session,
    notification_data: NotificationCreate,
    template_context: Optional[Dict[str, Any]] = None
) -> Notification:
    """Créer une notification"""
    
    # Vérifier les préférences utilisateur
    preferences = get_user_notification_preferences(db, notification_data.user_id)
    
    # Déterminer quels canaux utiliser
    channels_to_send = []
    for channel in notification_data.channels:
        if preferences.should_send_notification(notification_data.notification_type.value, channel.value):
            channels_to_send.append(channel)
    
    # Si aucun canal n'est autorisé, ne pas créer la notification
    if not channels_to_send:
        return None
    
    # Créer notification
    notification = Notification(
        user_id=notification_data.user_id,
        title=notification_data.title,
        message=notification_data.message,
        notification_type=notification_data.notification_type,
        priority=notification_data.priority,
        entity_type=notification_data.entity_type,
        entity_id=notification_data.entity_id,
        action_url=notification_data.action_url,
        action_label=notification_data.action_label,
        notification_metadata=notification_data.notification_metadata,
        is_actionable=notification_data.is_actionable,
        expires_at=notification_data.expires_at,
        group_key=notification_data.group_key,
        sent_in_app="in_app" in [c.value for c in channels_to_send],
        sent_email="email" in [c.value for c in channels_to_send],
        sent_push="push" in [c.value for c in channels_to_send],
        sent_sms="sms" in [c.value for c in channels_to_send]
    )
    
    db.add(notification)
    db.commit()
    db.refresh(notification)
    
    # TODO: Envoyer via les canaux appropriés
    # _send_via_channels(notification, channels_to_send)
    
    return notification

def create_notification_from_template(
    db: Session,
    template_id: UUID,
    user_id: UUID,
    context: Dict[str, Any],
    channels: Optional[List[str]] = None
) -> Optional[Notification]:
    """Créer notification à partir d'un template"""
    
    template = db.query(NotificationTemplate).filter(
        NotificationTemplate.template_id == template_id,
        NotificationTemplate.is_active == True
    ).first()
    
    if not template:
        return None
    
    try:
        # Rendre le contenu
        rendered = template.render_content(context)
        
        # Utiliser canaux du template si non spécifiés
        if not channels:
            channels = template.default_channels
        
        # Créer notification
        notification_data = NotificationCreate(
            user_id=user_id,
            title=rendered["title"],
            message=rendered["message"],
            notification_type=template.notification_type,
            priority=template.priority,
            action_url=rendered.get("action_url"),
            action_label=rendered.get("action_label"),
            channels=channels,
            notification_metadata=context
        )
        
        notification = create_notification(db, notification_data, context)
        
        # Mettre à jour stats du template
        template.usage_count += 1
        template.last_used_at = datetime.utcnow()
        db.commit()
        
        return notification
        
    except ValueError as e:
        print(f"Erreur rendu template {template_id}: {e}")
        return None

def bulk_create_notifications(
    db: Session,
    bulk_data: BulkNotificationCreate
) -> Tuple[int, int, List[UUID]]:
    """Créer notifications en masse"""
    
    sent_count = 0
    failed_count = 0
    failed_users = []
    
    for user_id in bulk_data.user_ids:
        try:
            notification_data = NotificationCreate(
                user_id=user_id,
                title=bulk_data.title,
                message=bulk_data.message,
                notification_type=bulk_data.notification_type,
                priority=bulk_data.priority,
                channels=bulk_data.channels,
                entity_type=bulk_data.entity_type,
                entity_id=bulk_data.entity_id,
                action_url=bulk_data.action_url,
                action_label=bulk_data.action_label,
                notification_metadata=bulk_data.notification_metadata
            )
            
            notification = create_notification(db, notification_data)
            if notification:
                sent_count += 1
            else:
                failed_count += 1
                failed_users.append(user_id)
                
        except Exception as e:
            print(f"Erreur création notification pour {user_id}: {e}")
            failed_count += 1
            failed_users.append(user_id)
    
    return sent_count, failed_count, failed_users

def get_user_notifications(
    db: Session,
    user_id: UUID,
    unread_only: bool = False,
    include_archived: bool = False,
    limit: int = 50,
    skip: int = 0
) -> List[Notification]:
    """Récupérer notifications d'un utilisateur"""
    
    query = db.query(Notification).filter(Notification.user_id == user_id)
    
    if unread_only:
        query = query.filter(Notification.is_read == False)
    
    if not include_archived:
        query = query.filter(Notification.is_archived == False)
    
    # Exclure notifications expirées
    query = query.filter(
        or_(
            Notification.expires_at.is_(None),
            Notification.expires_at > datetime.utcnow()
        )
    )
    
    return query.order_by(desc(Notification.created_at)).offset(skip).limit(limit).all()

def get_notification_by_id(
   db: Session,
   notification_id: UUID,
   user_id: Optional[UUID] = None
) -> Optional[Notification]:
   """Récupérer notification par ID"""
   
   query = db.query(Notification).filter(Notification.notification_id == notification_id)
   
   if user_id:
       query = query.filter(Notification.user_id == user_id)
   
   return query.first()

def update_notification(
   db: Session,
   notification_id: UUID,
   update_data: NotificationUpdate,
   user_id: Optional[UUID] = None
) -> Optional[Notification]:
   """Mettre à jour notification"""
   
   query = db.query(Notification).filter(Notification.notification_id == notification_id)
   
   if user_id:
       query = query.filter(Notification.user_id == user_id)
   
   notification = query.first()
   
   if not notification:
       return None
   
   # Mettre à jour champs
   for field, value in update_data.dict(exclude_unset=True).items():
       if hasattr(notification, field):
           setattr(notification, field, value)
   
   # Marquer heure de lecture si lu
   if update_data.is_read and not notification.read_at:
       notification.read_at = datetime.utcnow()
   
   db.commit()
   db.refresh(notification)
   return notification

def mark_notification_as_read(
   db: Session,
   notification_id: UUID,
   user_id: UUID
) -> bool:
   """Marquer notification comme lue"""
   
   notification = update_notification(
       db, notification_id, 
       NotificationUpdate(is_read=True), 
       user_id
   )
   return notification is not None

def mark_all_notifications_as_read(db: Session, user_id: UUID) -> int:
   """Marquer toutes les notifications comme lues"""
   
   count = db.query(Notification).filter(
       Notification.user_id == user_id,
       Notification.is_read == False
   ).update({
       "is_read": True,
       "read_at": datetime.utcnow()
   })
   
   db.commit()
   return count

def archive_notification(
   db: Session,
   notification_id: UUID,
   user_id: UUID
) -> bool:
   """Archiver notification"""
   
   notification = update_notification(
       db, notification_id,
       NotificationUpdate(is_archived=True),
       user_id
   )
   return notification is not None

def delete_notification(
   db: Session,
   notification_id: UUID,
   user_id: Optional[UUID] = None
) -> bool:
   """Supprimer notification"""
   
   query = db.query(Notification).filter(Notification.notification_id == notification_id)
   
   if user_id:
       query = query.filter(Notification.user_id == user_id)
   
   notification = query.first()
   
   if not notification:
       return False
   
   db.delete(notification)
   db.commit()
   return True

def search_notifications(
   db: Session,
   user_id: UUID,
   filters: NotificationFilter,
   skip: int = 0,
   limit: int = 20
) -> Tuple[List[Notification], int]:
   """Rechercher notifications avec filtres"""
   
   query = db.query(Notification).filter(Notification.user_id == user_id)
   
   # Appliquer filtres
   if filters.notification_type:
       query = query.filter(Notification.notification_type == filters.notification_type)
   
   if filters.priority:
       query = query.filter(Notification.priority == filters.priority)
   
   if filters.is_read is not None:
       query = query.filter(Notification.is_read == filters.is_read)
   
   if filters.is_archived is not None:
       query = query.filter(Notification.is_archived == filters.is_archived)
   
   if filters.is_actionable is not None:
       query = query.filter(Notification.is_actionable == filters.is_actionable)
   
   if filters.entity_type:
       query = query.filter(Notification.entity_type == filters.entity_type)
   
   if filters.date_from:
       query = query.filter(Notification.created_at >= filters.date_from)
   
   if filters.date_to:
       query = query.filter(Notification.created_at <= filters.date_to)
   
   # Compter total
   total_count = query.count()
   
   # Récupérer résultats paginés
   notifications = query.order_by(desc(Notification.created_at)).offset(skip).limit(limit).all()
   
   return notifications, total_count

def get_notification_counts(db: Session, user_id: UUID) -> Dict[str, int]:
   """Comptes de notifications"""
   
   base_query = db.query(Notification).filter(
       Notification.user_id == user_id,
       Notification.is_archived == False,
       or_(
           Notification.expires_at.is_(None),
           Notification.expires_at > datetime.utcnow()
       )
   )
   
   total = base_query.count()
   unread = base_query.filter(Notification.is_read == False).count()
   urgent = base_query.filter(Notification.priority == NotificationPriority.urgent).count()
   actionable = base_query.filter(Notification.is_actionable == True).count()
   
   return {
       "total": total,
       "unread": unread,
       "urgent": urgent,
       "actionable": actionable
   }

# ========== CRUD PREFERENCES ==========

def get_user_notification_preferences(
   db: Session,
   user_id: UUID
) -> UserNotificationPreferences:
   """Récupérer préférences utilisateur (créer si inexistantes)"""
   
   preferences = db.query(UserNotificationPreferences).filter(
       UserNotificationPreferences.user_id == user_id
   ).first()
   
   if not preferences:
       # Créer préférences par défaut
       preferences = UserNotificationPreferences(user_id=user_id)
       db.add(preferences)
       db.commit()
       db.refresh(preferences)
   
   return preferences

def update_user_notification_preferences(
   db: Session,
   user_id: UUID,
   update_data: UserNotificationPreferencesUpdate
) -> UserNotificationPreferences:
   """Mettre à jour préférences"""
   
   preferences = get_user_notification_preferences(db, user_id)
   
   for field, value in update_data.dict(exclude_unset=True).items():
       if hasattr(preferences, field):
           setattr(preferences, field, value)
   
   preferences.updated_at = datetime.utcnow()
   
   db.commit()
   db.refresh(preferences)
   return preferences

# ========== CRUD TEMPLATES ==========

def create_notification_template(
   db: Session,
   template_data: Dict[str, Any],
   created_by: Optional[UUID] = None
) -> NotificationTemplate:
   """Créer template de notification"""
   
   template = NotificationTemplate(
       **template_data,
       created_by=created_by
   )
   
   db.add(template)
   db.commit()
   db.refresh(template)
   return template

def get_notification_templates(
   db: Session,
   notification_type: Optional[NotificationType] = None,
   active_only: bool = True
) -> List[NotificationTemplate]:
   """Récupérer templates"""
   
   query = db.query(NotificationTemplate)
   
   if notification_type:
       query = query.filter(NotificationTemplate.notification_type == notification_type)
   
   if active_only:
       query = query.filter(NotificationTemplate.is_active == True)
   
   return query.order_by(NotificationTemplate.name).all()

# ========== STATISTIQUES ==========

def get_notification_stats(db: Session, user_id: UUID) -> Dict[str, Any]:
   """Statistiques de notifications"""
   
   # Stats générales
   total_sent = db.query(Notification).filter(Notification.user_id == user_id).count()
   total_read = db.query(Notification).filter(
       Notification.user_id == user_id,
       Notification.is_read == True
   ).count()
   total_archived = db.query(Notification).filter(
       Notification.user_id == user_id,
       Notification.is_archived == True
   ).count()
   
   read_rate = (total_read / total_sent * 100) if total_sent > 0 else 0
   
   # Temps moyen de lecture
   read_notifications = db.query(Notification).filter(
       Notification.user_id == user_id,
       Notification.is_read == True,
       Notification.read_at.isnot(None)
   ).all()
   
   if read_notifications:
       read_times = [(n.read_at - n.created_at).total_seconds() / 3600 for n in read_notifications]
       avg_read_time = sum(read_times) / len(read_times)
   else:
       avg_read_time = 0
   
   # Notifications par type
   type_counts = db.query(
       Notification.notification_type,
       func.count(Notification.notification_id)
   ).filter(
       Notification.user_id == user_id
   ).group_by(Notification.notification_type).all()
   
   notifications_by_type = {str(nt): count for nt, count in type_counts}
   
   # Notifications par priorité
   priority_counts = db.query(
       Notification.priority,
       func.count(Notification.notification_id)
   ).filter(
       Notification.user_id == user_id
   ).group_by(Notification.priority).all()
   
   notifications_by_priority = {str(p): count for p, count in priority_counts}
   
   # Stats de livraison
   delivery_stats = {
       "in_app": db.query(Notification).filter(
           Notification.user_id == user_id,
           Notification.sent_in_app == True
       ).count(),
       "email": db.query(Notification).filter(
           Notification.user_id == user_id,
           Notification.sent_email == True
       ).count(),
       "push": db.query(Notification).filter(
           Notification.user_id == user_id,
           Notification.sent_push == True
       ).count(),
       "sms": db.query(Notification).filter(
           Notification.user_id == user_id,
           Notification.sent_sms == True
       ).count()
   }
   
   return {
       "total_sent": total_sent,
       "total_read": total_read,
       "total_archived": total_archived,
       "read_rate": round(read_rate, 2),
       "average_read_time_hours": round(avg_read_time, 2),
       "notifications_by_type": notifications_by_type,
       "notifications_by_priority": notifications_by_priority,
       "delivery_stats": delivery_stats
   }

# ========== FONCTIONS UTILITAIRES ==========

def cleanup_expired_notifications(db: Session) -> int:
   """Nettoyer notifications expirées"""
   
   expired_count = db.query(Notification).filter(
       Notification.expires_at < datetime.utcnow()
   ).delete()
   
   db.commit()
   return expired_count

def auto_archive_old_notifications(db: Session) -> int:
   """Archiver automatiquement anciennes notifications"""
   
   cutoff_date = datetime.utcnow() - timedelta(days=30)
   
   # Archiver notifications lues de plus de 30 jours
   archived_count = db.query(Notification).filter(
       Notification.is_read == True,
       Notification.created_at < cutoff_date,
       Notification.is_archived == False
   ).update({"is_archived": True})
   
   # Archiver notifications non lues de plus de 7 jours
   old_cutoff = datetime.utcnow() - timedelta(days=7)
   archived_count += db.query(Notification).filter(
       Notification.is_read == False,
       Notification.created_at < old_cutoff,
       Notification.is_archived == False
   ).update({"is_archived": True})
   
   db.commit()
   return archived_count

def group_similar_notifications(
   db: Session,
   user_id: UUID,
   notification_type: NotificationType,
   group_key: str,
   max_age_hours: int = 24
) -> Optional[Notification]:
   """Grouper notifications similaires"""
   
   cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
   
   # Chercher notification existante dans le groupe
   existing = db.query(Notification).filter(
       Notification.user_id == user_id,
       Notification.notification_type == notification_type,
       Notification.group_key == group_key,
       Notification.created_at > cutoff_time,
       Notification.is_read == False
   ).first()
   
   return existing

def send_notification_digest(db: Session, user_id: UUID) -> bool:
   """Envoyer digest des notifications par email"""
   
   preferences = get_user_notification_preferences(db, user_id)
   
   if not preferences.email_digest_enabled:
       return False
   
   # Récupérer notifications non lues récentes
   cutoff_time = datetime.utcnow() - timedelta(days=1)
   notifications = db.query(Notification).filter(
       Notification.user_id == user_id,
       Notification.is_read == False,
       Notification.created_at > cutoff_time,
       Notification.sent_email == False  # Pas encore envoyées par email
   ).all()
   
   if not notifications:
       return False
   
   # TODO: Construire et envoyer email digest
   # _send_email_digest(user_id, notifications)
   
   # Marquer comme envoyées par email
   for notification in notifications:
       notification.sent_email = True
   
   db.commit()
   return True

# ========== HELPERS POUR TYPES SPÉCIFIQUES ==========

def create_message_notification(
   db: Session,
   recipient_id: UUID,
   sender_name: str,
   message_preview: str,
   message_id: UUID
) -> Optional[Notification]:
   """Créer notification de message reçu"""
   
   notification_data = NotificationCreate(
       user_id=recipient_id,
       title=f"Nouveau message de {sender_name}",
       message=f"Message: {message_preview[:100]}...",
       notification_type=NotificationType.message_received,
       entity_type="message",
       entity_id=message_id,
       action_url=f"/messages/{message_id}",
       action_label="Voir le message",
       channels=[NotificationChannel.in_app, NotificationChannel.push],
       notification_metadata={"sender_name": sender_name}
   )
   
   return create_notification(db, notification_data)

def create_call_reminder_notification(
   db: Session,
   participant_id: UUID,
   call_title: str,
   call_id: UUID,
   minutes_before: int
) -> Optional[Notification]:
   """Créer rappel d'appel"""
   
   notification_data = NotificationCreate(
       user_id=participant_id,
       title=f"Rappel: {call_title}",
       message=f"Votre appel commence dans {minutes_before} minutes",
       notification_type=NotificationType.call_reminder,
       priority=NotificationPriority.high,
       entity_type="call",
       entity_id=call_id,
       action_url=f"/calls/{call_id}",
       action_label="Rejoindre l'appel",
       channels=[NotificationChannel.in_app, NotificationChannel.push],
       notification_metadata={"minutes_before": minutes_before}
   )
   
   return create_notification(db, notification_data)

def create_assignment_due_notification(
   db: Session,
   student_id: UUID,
   assignment_title: str,
   assignment_id: UUID,
   due_date: datetime
) -> Optional[Notification]:
   """Créer notification d'échéance de devoir"""
   
   days_left = (due_date - datetime.utcnow()).days
   
   if days_left <= 0:
       message = f"Le devoir '{assignment_title}' est dû aujourd'hui !"
       priority = NotificationPriority.urgent
   elif days_left == 1:
       message = f"Le devoir '{assignment_title}' est dû demain"
       priority = NotificationPriority.high
   else:
       message = f"Le devoir '{assignment_title}' est dû dans {days_left} jours"
       priority = NotificationPriority.normal
   
   notification_data = NotificationCreate(
       user_id=student_id,
       title="Échéance de devoir",
       message=message,
       notification_type=NotificationType.assignment_due_soon,
       priority=priority,
       entity_type="assignment",
       entity_id=assignment_id,
       action_url=f"/assignments/{assignment_id}",
       action_label="Voir le devoir",
       channels=[NotificationChannel.in_app, NotificationChannel.email],
       notification_metadata={"days_left": days_left}
   )
   
   return create_notification(db, notification_data)