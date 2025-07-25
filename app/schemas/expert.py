from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, date
from app.schemas.user import UserResponse, UserCreate

class ExpertBase(BaseModel):
    specialization: str
    years_of_experience: Optional[int] = None
    linkedin_profile: Optional[HttpUrl] = None
    cv_url: Optional[HttpUrl] = None
    bio: Optional[str] = None
    hourly_rate: Optional[int] = None
    is_active: Optional[bool] = True

class ExpertCreate(ExpertBase):
    user: UserCreate

class ExpertUpdate(ExpertBase):
    specialization: Optional[str] = None
    years_of_experience: Optional[int] = None
    linkedin_profile: Optional[HttpUrl] = None
    cv_url: Optional[HttpUrl] = None
    bio: Optional[str] = None
    hourly_rate: Optional[int] = None
    is_active: Optional[bool] = None

class ExpertProfileUpdate(BaseModel):
    """Mise à jour profil expert (sans user)"""
    specialization: Optional[str] = None
    years_of_experience: Optional[int] = None
    linkedin_profile: Optional[str] = None
    cv_url: Optional[str] = None
    bio: Optional[str] = None
    hourly_rate: Optional[int] = None

class ExpertResponse(BaseModel):
    expert_id: UUID
    user: UserResponse
    specialization: str
    years_of_experience: Optional[int] = None
    linkedin_profile: Optional[HttpUrl] = None
    cv_url: Optional[HttpUrl] = None
    bio: Optional[str] = None
    hourly_rate: Optional[int] = None
    is_active: bool

class ExpertOut(ExpertBase):
    expert_id: UUID

    class Config:
        from_attributes = True

# Nouveaux schémas pour le dashboard expert

class ExpertStats(BaseModel):
    """Statistiques expert"""
    profile_completion: int
    is_active: bool
    specialization: str
    years_of_experience: int
    
    # Stats d'activité
    programs_assigned: int
    active_programs: int
    entrepreneurs_mentored: int
    modules_created: int
    assignments_created: int
    total_sessions: int
    average_rating: float
    
    # Stats temporelles
    this_month_sessions: int
    this_week_sessions: int

class ExpertActivity(BaseModel):
    """Activité récente expert"""
    activity_type: str  # "session", "module_creation", "assignment_creation", "mentoring"
    title: str
    description: str
    date: datetime
    related_id: Optional[str] = None

class ExpertNotification(BaseModel):
    """Notification expert"""
    notification_type: str  # "info", "success", "warning", "error"
    title: str
    message: str
    date: datetime
    is_read: bool = False
    action_url: Optional[str] = None

class ExpertQuickAction(BaseModel):
    """Action rapide expert"""
    action_type: str  # "complete_profile", "create_module", "schedule_session", "review_assignments"
    title: str
    description: str
    priority: str  # "high", "medium", "low"
    action_url: str

class ExpertProgram(BaseModel):
    """Programme assigné à un expert"""
    program_id: UUID
    program_name: str
    participants_count: int
    start_date: date
    end_date: date
    is_active: bool
    role: str  # "mentor", "instructor", "reviewer"

class ExpertEntrepreneur(BaseModel):
    """Entrepreneur accompagné"""
    entrepreneur_id: UUID
    entrepreneur_name: str
    company_name: str
    industry_sector: Optional[str]
    enrollment_date: datetime
    progress_percentage: float
    last_interaction: Optional[datetime]

class ExpertDashboard(BaseModel):
    """Dashboard expert complet"""
    expert: ExpertResponse
    stats: ExpertStats
    
    # Programmes et entrepreneurs
    assigned_programs: List[ExpertProgram] = []
    mentored_entrepreneurs: List[ExpertEntrepreneur] = []
    
    # Activités et notifications
    recent_activities: List[ExpertActivity] = []
    notifications: List[ExpertNotification] = []
    quick_actions: List[ExpertQuickAction] = []
    
    # Métriques
    monthly_performance: Dict[str, Any] = {}
    upcoming_sessions: List[Dict[str, Any]] = []

class ExpertPublicProfile(BaseModel):
    """Profil public expert (pour annuaire)"""
    expert_id: UUID
    name: str
    specialization: str
    years_of_experience: Optional[int]
    bio: Optional[str]
    average_rating: float
    total_sessions: int
    linkedin_profile: Optional[str]
    is_available: bool

class ExpertLeaderboardEntry(BaseModel):
    """Entrée du classement experts"""
    expert_id: UUID
    name: str
    specialization: str
    score: float
    years_experience: int
    programs_count: int
    rating: float
    rank: int