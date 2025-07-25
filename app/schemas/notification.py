from pydantic import BaseModel, UUID4
from typing import Optional, List, Dict, Any
from datetime import datetime, time
from enum import Enum

class NotificationType(str, Enum):
    message_received = "message_received"
    message_reply = "message_reply"
    message_mention = "message_mention"
    program_accepted = "program_accepted"
    program_rejected = "program_rejected"
    program_started = "program_started"
    program_completed = "program_completed"
    module_assigned = "module_assigned"
    module_completed = "module_completed"
    assignment_assigned = "assignment_assigned"
    assignment_due_soon = "assignment_due_soon"
    assignment_graded = "assignment_graded"
    assignment_overdue = "assignment_overdue"
    call_scheduled = "call_scheduled"
    call_reminder = "call_reminder"
    call_cancelled = "call_cancelled"
    call_started = "call_started"
    call_missed = "call_missed"
    expert_application = "expert_application"
    expert_approved = "expert_approved"
    expert_assigned = "expert_assigned"
    entrepreneur_application = "entrepreneur_application"
    entrepreneur_profile_incomplete = "entrepreneur_profile_incomplete"
    system_maintenance = "system_maintenance"
    system_update = "system_update"
    account_security = "account_security"
    payment_reminder = "payment_reminder"
    follow_request = "follow_request"
    new_follower = "new_follower"
    achievement_unlocked = "achievement_unlocked"

class NotificationPriority(str, Enum):
    low = "low"
    normal = "normal"
    high = "high"
    urgent = "urgent"

class NotificationChannel(str, Enum):
    in_app = "in_app"
    email = "email"
    push = "push"
    sms = "sms"

# Schémas Notification
class NotificationBase(BaseModel):
    title: str
    message: str
    notification_type: NotificationType
    priority: NotificationPriority = NotificationPriority.normal
    entity_type: Optional[str] = None
    entity_id: Optional[UUID4] = None
    action_url: Optional[str] = None
    action_label: Optional[str] = None
    notification_metadata: Optional[Dict[str, Any]] = {}
    is_actionable: bool = False
    expires_at: Optional[datetime] = None

class NotificationCreate(NotificationBase):
    user_id: UUID4
    channels: Optional[List[NotificationChannel]] = [NotificationChannel.in_app]
    group_key: Optional[str] = None

class NotificationUpdate(BaseModel):
    is_read: Optional[bool] = None
    is_archived: Optional[bool] = None
    action_taken: Optional[bool] = None

class NotificationResponse(NotificationBase):
    notification_id: UUID4
    user_id: UUID4
    is_read: bool
    is_archived: bool
    action_taken: bool
    sent_in_app: bool
    sent_email: bool
    sent_push: bool
    sent_sms: bool
    created_at: datetime
    read_at: Optional[datetime] = None
    group_key: Optional[str] = None
    parent_notification_id: Optional[UUID4] = None
    delivery_attempts: int
    delivery_failed: bool
    
    # Propriétés calculées
    is_expired: bool = False
    age_hours: float = 0.0

    class Config:
        from_attributes = True

# Schémas pour préférences
class UserNotificationPreferencesBase(BaseModel):
    notifications_enabled: bool = True
    email_notifications: bool = True
    push_notifications: bool = True
    sms_notifications: bool = False
    quiet_hours_enabled: bool = False
    quiet_hours_start: time = time(22, 0)
    quiet_hours_end: time = time(8, 0)
    quiet_days: List[int] = []
    email_digest_enabled: bool = True
    email_digest_frequency: str = "daily"
    email_digest_time: time = time(9, 0)
    group_similar_notifications: bool = True
    max_notifications_per_hour: int = 10
    marketing_emails: bool = False
    newsletter_subscription: bool = False

class UserNotificationPreferencesUpdate(UserNotificationPreferencesBase):
    type_preferences: Optional[Dict[str, Dict[str, bool]]] = None

class UserNotificationPreferencesResponse(UserNotificationPreferencesBase):
    preference_id: UUID4
    user_id: UUID4
    type_preferences: Dict[str, Dict[str, bool]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Schémas pour templates
class NotificationTemplateBase(BaseModel):
    name: str
    notification_type: NotificationType
    description: Optional[str] = None
    title_template: str
    message_template: str
    email_subject_template: Optional[str] = None
    email_body_template: Optional[str] = None
    push_title_template: Optional[str] = None
    push_body_template: Optional[str] = None
    priority: NotificationPriority = NotificationPriority.normal
    default_channels: List[NotificationChannel] = [NotificationChannel.in_app]
    action_url_template: Optional[str] = None
    action_label: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = {}
    user_preferences_key: Optional[str] = None

class NotificationTemplateCreate(NotificationTemplateBase):
    pass

class NotificationTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    title_template: Optional[str] = None
    message_template: Optional[str] = None
    email_subject_template: Optional[str] = None
    email_body_template: Optional[str] = None
    push_title_template: Optional[str] = None
    push_body_template: Optional[str] = None
    priority: Optional[NotificationPriority] = None
    default_channels: Optional[List[NotificationChannel]] = None
    action_url_template: Optional[str] = None
    action_label: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class NotificationTemplateResponse(NotificationTemplateBase):
    template_id: UUID4
    is_active: bool
    is_system: bool
    created_by: Optional[UUID4] = None
    created_at: datetime
    updated_at: datetime
    usage_count: int
    last_used_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Schémas pour listes et stats
class NotificationSummary(BaseModel):
    total_notifications: int
    unread_count: int
    urgent_count: int
    actionable_count: int
    recent_notifications: List[NotificationResponse]

class NotificationStats(BaseModel):
    total_sent: int
    total_read: int
    total_archived: int
    read_rate: float
    average_read_time_hours: float
    notifications_by_type: Dict[str, int]
    notifications_by_priority: Dict[str, int]
    delivery_stats: Dict[str, int]

class BulkNotificationCreate(BaseModel):
    user_ids: List[UUID4]
    title: str
    message: str
    notification_type: NotificationType
    priority: NotificationPriority = NotificationPriority.normal
    channels: List[NotificationChannel] = [NotificationChannel.in_app]
    entity_type: Optional[str] = None
    entity_id: Optional[UUID4] = None
    action_url: Optional[str] = None
    action_label: Optional[str] = None
    notification_metadata: Optional[Dict[str, Any]] = {}

class BulkNotificationResponse(BaseModel):
    sent_count: int
    failed_count: int
    failed_users: List[UUID4] = []

# Schémas pour filtres
class NotificationFilter(BaseModel):
    notification_type: Optional[NotificationType] = None
    priority: Optional[NotificationPriority] = None
    is_read: Optional[bool] = None
    is_archived: Optional[bool] = None
    is_actionable: Optional[bool] = None
    entity_type: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

class NotificationSearchResult(BaseModel):
    notifications: List[NotificationResponse]
    total_count: int
    search_time_ms: float