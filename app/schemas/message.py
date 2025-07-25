from pydantic import BaseModel, UUID4
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class MessageType(str, Enum):
    direct = "direct"
    group = "group"
    announcement = "announcement"
    system = "system"

class MessageStatus(str, Enum):
    sent = "sent"
    delivered = "delivered"
    read = "read"
    failed = "failed"

class MessagePriority(str, Enum):
    low = "low"
    normal = "normal"
    high = "high"
    urgent = "urgent"

# Schémas de base
class MessageBase(BaseModel):
    subject: Optional[str] = None
    message_text: str
    message_type: MessageType = MessageType.direct
    priority: MessagePriority = MessagePriority.normal
    program_id: Optional[UUID4] = None
    expires_at: Optional[datetime] = None

class MessageCreate(MessageBase):
    receiver_id: Optional[UUID4] = None  # Optionnel pour messages de groupe
    parent_message_id: Optional[UUID4] = None
    attachment_files: Optional[List[str]] = []  # Liste des URLs de fichiers

class MessageUpdate(BaseModel):
    subject: Optional[str] = None
    message_text: Optional[str] = None
    priority: Optional[MessagePriority] = None
    is_starred: Optional[bool] = None
    is_archived: Optional[bool] = None

class MessageResponse(MessageBase):
    message_id: UUID4
    sender_id: UUID4
    receiver_id: Optional[UUID4] = None
    sender_name: str
    receiver_name: Optional[str] = None
    
    # États et statuts
    status: MessageStatus
    is_read: bool
    is_starred: bool
    is_archived: bool
    is_deleted_by_sender: bool
    is_deleted_by_receiver: bool
    
    # Temporalité
    sent_at: datetime
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    last_edited_at: Optional[datetime] = None
    
    # Métadonnées
    conversation_id: Optional[str] = None
    parent_message_id: Optional[UUID4] = None
    edit_count: int = 0
    program_name: Optional[str] = None
    
    # Attachments et interactions
    attachments: List['MessageAttachmentResponse'] = []
    reactions: List['MessageReactionResponse'] = []
    reply_count: int = 0
    
    # Propriétés calculées
    is_group_message: bool = False
    conversation_identifier: str

    class Config:
        from_attributes = True

# Schémas pour les réactions
class MessageReactionCreate(BaseModel):
    emoji: str
    reaction_type: str  # like, love, laugh, etc.

class MessageReactionResponse(BaseModel):
    reaction_id: UUID4
    message_id: UUID4
    user_id: UUID4
    user_name: str
    emoji: str
    reaction_type: str
    created_at: datetime

    class Config:
        from_attributes = True

# Schémas pour les pièces jointes
class MessageAttachmentResponse(BaseModel):
    attachment_id: UUID4
    message_id: UUID4
    file_name: str
    original_file_name: str
    file_url: str
    file_size: int
    content_type: str
    file_extension: Optional[str] = None
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    uploaded_at: datetime
    is_image: bool
    file_size_mb: float

    class Config:
        from_attributes = True

# Schémas pour les conversations
class ConversationParticipant(BaseModel):
    user_id: UUID4
    name: str
    user_type: str
    avatar_url: Optional[str] = None
    is_online: bool = False
    last_seen: Optional[datetime] = None

class ConversationResponse(BaseModel):
    conversation_id: UUID4
    conversation_key: str
    title: Optional[str] = None
    conversation_type: str
    participants: List[ConversationParticipant]
    participant_count: int
    message_count: int
    unread_count: int
    last_message: Optional[MessageResponse] = None
    last_activity_at: datetime
    is_muted: bool
    is_active: bool

class ConversationSummary(BaseModel):
    total_conversations: int
    unread_messages: int
    active_conversations: List[ConversationResponse]
    recent_messages: List[MessageResponse]

# Schémas pour les threads (fils de discussion)
class MessageThread(BaseModel):
    parent_message: MessageResponse
    replies: List[MessageResponse]
    total_replies: int
    participants: List[ConversationParticipant]

# Schémas pour la recherche
class MessageSearchResult(BaseModel):
    messages: List[MessageResponse]
    total_count: int
    conversations_found: List[ConversationResponse]
    search_time_ms: float

class MessageSearchFilters(BaseModel):
    query: Optional[str] = None
    sender_id: Optional[UUID4] = None
    conversation_id: Optional[str] = None
    message_type: Optional[MessageType] = None
    has_attachments: Optional[bool] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    is_starred: Optional[bool] = None

# Schémas pour les statistiques
class MessageStats(BaseModel):
    total_sent: int
    total_received: int
    unread_count: int
    active_conversations: int
    messages_this_week: int
    messages_this_month: int
    response_rate: float
    average_response_time_hours: float
    most_active_conversation: Optional[str] = None
    attachment_count: int
    reactions_given: int
    reactions_received: int

# Schémas pour les notifications
class MessageNotification(BaseModel):
    notification_id: UUID4
    message: MessageResponse
    notification_type: str  # new_message, message_read, reaction_added
    created_at: datetime
    is_read: bool = False

# Schémas pour la configuration utilisateur
class MessageSettings(BaseModel):
    email_notifications: bool = True
    push_notifications: bool = True
    sound_notifications: bool = True
    notification_schedule_start: Optional[str] = "08:00"  # Format HH:MM
    notification_schedule_end: Optional[str] = "22:00"
    muted_conversations: List[str] = []
    auto_read_receipts: bool = True
    typing_indicators: bool = True

# Schémas pour le chat en temps réel
class TypingIndicator(BaseModel):
    conversation_id: str
    user_id: UUID4
    user_name: str
    is_typing: bool
    timestamp: datetime

class MessageDeliveryStatus(BaseModel):
    message_id: UUID4
    status: MessageStatus
    delivered_to: List[UUID4] = []
    read_by: List[UUID4] = []
    failed_for: List[UUID4] = []

# Mise à jour des forward references
MessageResponse.model_rebuild()