from pydantic import BaseModel, UUID4
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from enum import Enum

class CallType(str, Enum):
    one_on_one = "one_on_one"
    group_session = "group_session"
    webinar = "webinar"
    workshop = "workshop"
    office_hours = "office_hours"

class CallStatus(str, Enum):
    scheduled = "scheduled"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"
    no_show = "no_show"

class CallPriority(str, Enum):
    low = "low"
    normal = "normal"
    high = "high"
    urgent = "urgent"

class ParticipantRole(str, Enum):
    host = "host"
    co_host = "co_host"
    participant = "participant"
    observer = "observer"

class ParticipantStatus(str, Enum):
    invited = "invited"
    confirmed = "confirmed"
    declined = "declined"
    attended = "attended"
    no_show = "no_show"
    left_early = "left_early"

# Schémas Call
class CallBase(BaseModel):
    title: str
    description: Optional[str] = None
    agenda: Optional[str] = None
    call_type: CallType
    priority: CallPriority = CallPriority.normal
    scheduled_start: datetime
    scheduled_end: datetime
    timezone: str = "UTC"
    max_participants: Optional[int] = None
    requires_approval: bool = False
    is_recorded: bool = False
    platform: str = "zoom"
    reminder_minutes_before: int = 15

class CallCreate(CallBase):
    program_id: Optional[UUID4] = None
    module_id: Optional[UUID4] = None
    expert_id: Optional[UUID4] = None  # Si spécifié, sinon utilise l'expert connecté
    participant_ids: Optional[List[UUID4]] = []  # Participants à inviter directement

class CallUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    agenda: Optional[str] = None
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    timezone: Optional[str] = None
    max_participants: Optional[int] = None
    requires_approval: Optional[bool] = None
    is_recorded: Optional[bool] = None
    platform: Optional[str] = None
    status: Optional[CallStatus] = None
    meeting_url: Optional[str] = None
    meeting_password: Optional[str] = None
    summary: Optional[str] = None
    next_steps: Optional[str] = None

class CallResponse(CallBase):
    call_id: UUID4
    program_id: Optional[UUID4] = None
    module_id: Optional[UUID4] = None
    expert_id: UUID4
    created_by: UUID4
    status: CallStatus
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    actual_duration_minutes: Optional[int] = None
    meeting_url: Optional[str] = None
    meeting_id: Optional[str] = None
    meeting_password: Optional[str] = None
    is_recurring: bool = False
    participant_count: int = 0
    attendance_rate: float = 0.0
    satisfaction_score: Optional[float] = None
    summary: Optional[str] = None
    next_steps: Optional[str] = None
    follow_up_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    # Données enrichies
    expert_name: Optional[str] = None
    program_name: Optional[str] = None
    module_title: Optional[str] = None
    creator_name: Optional[str] = None
    
    # Propriétés calculées
    is_upcoming: bool = False
    is_live: bool = False
    is_past: bool = False
    can_join: bool = False
    time_until_start_minutes: Optional[int] = None
    
    # Participation utilisateur
    user_participation: Optional['CallParticipantResponse'] = None

    class Config:
        from_attributes = True

# Schémas CallParticipant
class CallParticipantBase(BaseModel):
    role: ParticipantRole = ParticipantRole.participant
    response_message: Optional[str] = None

class CallParticipantCreate(CallParticipantBase):
    call_id: UUID4
    user_id: UUID4

class CallParticipantUpdate(BaseModel):
    role: Optional[ParticipantRole] = None
    status: Optional[ParticipantStatus] = None
    response_message: Optional[str] = None
    satisfaction_rating: Optional[float] = None
    feedback: Optional[str] = None
    would_recommend: Optional[bool] = None
    follow_up_notes: Optional[str] = None

class CallParticipantResponse(CallParticipantBase):
    participant_id: UUID4
    call_id: UUID4
    user_id: UUID4
    entrepreneur_id: Optional[UUID4] = None
    expert_id: Optional[UUID4] = None
    status: ParticipantStatus
    invited_at: datetime
    invited_by: Optional[UUID4] = None
    responded_at: Optional[datetime] = None
    joined_at: Optional[datetime] = None
    left_at: Optional[datetime] = None
    actual_duration_minutes: Optional[int] = None
    camera_enabled: bool = True
    microphone_enabled: bool = True
    screen_sharing_used: bool = False
    questions_asked: int = 0
    messages_sent: int = 0
    polls_answered: int = 0
    satisfaction_rating: Optional[float] = None
    feedback: Optional[str] = None
    would_recommend: Optional[bool] = None
    follow_up_required: bool = False
    follow_up_notes: Optional[str] = None
    next_meeting_scheduled: Optional[datetime] = None
    
    # Données enrichies
    display_name: str
    user_type: Optional[str] = None
    company_name: Optional[str] = None
    
    # Propriétés calculées
    attended_full_session: bool = False
    engagement_score: float = 0.0

    class Config:
        from_attributes = True

# Schémas pour invitations
class CallInvitation(BaseModel):
    participant_ids: List[UUID4]
    message: Optional[str] = None
    send_email: bool = True
    send_notification: bool = True

class CallInvitationResponse(BaseModel):
    invited_count: int
    already_invited_count: int
    failed_invitations: List[Dict[str, str]] = []

# Schémas pour planning
class CallSchedule(BaseModel):
    """Planning d'appels"""
    date: datetime
    calls: List[CallResponse]
    total_calls: int
    total_duration_minutes: int

class CallCalendar(BaseModel):
    """Calendrier mensuel"""
    year: int
    month: int
    days: List[Dict[str, Any]]  # [{date, calls_count, has_conflicts}]
    total_calls: int

# Schémas pour récurrence
class RecurrencePattern(BaseModel):
    frequency: str  # daily, weekly, monthly
    interval: int = 1  # Tous les X (jours/semaines/mois)
    days_of_week: Optional[List[int]] = None  # Pour weekly [1,3,5] = lun,mer,ven
    day_of_month: Optional[int] = None  # Pour monthly
    end_date: Optional[datetime] = None
    max_occurrences: Optional[int] = None

class RecurringCallCreate(CallCreate):
    recurrence: RecurrencePattern

# Schémas pour templates
class CallTemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    call_type: CallType
    priority: CallPriority = CallPriority.normal
    default_duration_minutes: int = 60
    default_agenda: Optional[str] = None
    platform: str = "zoom"
    requires_approval: bool = False
    max_participants: Optional[int] = None
    is_recorded: bool = False

class CallTemplateCreate(CallTemplateBase):
    preparation_checklist: Optional[List[str]] = []
    default_questions: Optional[List[str]] = []

class CallTemplateResponse(CallTemplateBase):
    template_id: UUID4
    created_by: UUID4
    created_at: datetime
    updated_at: datetime
    is_active: bool
    usage_count: int
    preparation_checklist: Optional[List[str]] = []
    default_questions: Optional[List[str]] = []

    class Config:
        from_attributes = True

# Schémas pour statistiques
class CallStats(BaseModel):
    total_calls: int
    upcoming_calls: int
    completed_calls: int
    cancelled_calls: int
    total_participants: int
    average_duration_minutes: float
    average_attendance_rate: float
    average_satisfaction: float
    most_popular_time_slot: Optional[str] = None
    busiest_day_of_week: Optional[str] = None

class ParticipantStats(BaseModel):
    total_calls_attended: int
    total_hours_spent: float
    average_engagement_score: float
    calls_hosted: int = 0
    calls_as_participant: int = 0
    no_show_rate: float = 0.0
    average_satisfaction_given: float = 0.0

# Schémas pour les enregistrements
class CallRecordingResponse(BaseModel):
    recording_id: UUID4
    call_id: UUID4
    file_name: str
    file_url: str
    file_size: int
    duration_seconds: int
    format: str
    quality: str
    is_processed: bool
    is_available: bool
    is_transcribed: bool
    transcript_url: Optional[str] = None
    recorded_at: datetime
    view_count: int
    download_count: int
    duration_formatted: str
    file_size_mb: float

    class Config:
        from_attributes = True

# Schémas pour recherche et filtres
class CallFilter(BaseModel):
    call_type: Optional[CallType] = None
    status: Optional[CallStatus] = None
    program_id: Optional[UUID4] = None
    expert_id: Optional[UUID4] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    participant_id: Optional[UUID4] = None

class CallSearchResult(BaseModel):
    calls: List[CallResponse]
    total_count: int
    search_time_ms: float