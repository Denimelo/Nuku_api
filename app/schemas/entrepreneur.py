from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from uuid import UUID
from datetime import date, datetime
from enum import Enum
from app.schemas.user import UserCreate, UserResponse
from pydantic import UUID4
from app.schemas.program import ProgramWithParticipation
from typing import Dict, Any

class ValidationStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class EntrepreneurBase(BaseModel):
    # Champs existants
    company_name: str
    company_registration_number: Optional[str] = None
    company_description: Optional[str] = None
    industry_sector: Optional[str] = None
    founding_date: Optional[date] = None
    number_of_employees: Optional[int] = None
    annual_revenue: Optional[float] = None
    has_raised_funds: Optional[bool] = False
    amount_raised: Optional[float] = None
    wants_to_raise_funds: Optional[bool] = False
    desired_funding_amount: Optional[float] = None

    # 📎 Pièces jointes
    identity_card_url: Optional[HttpUrl] = None
    company_logo_url: Optional[HttpUrl] = None
    registration_document_url: Optional[HttpUrl] = None
    professional_card_url: Optional[HttpUrl] = None

    # 🔘 Niveau de maturité
    company_not_created: Optional[bool] = False
    company_recently_created: Optional[bool] = False
    company_established: Optional[bool] = False

class EntrepreneurCreate(EntrepreneurBase):
    user: UserCreate

class EntrepreneurUpdate(EntrepreneurBase):
    company_name: Optional[str] = None

class EntrepreneurResponse(BaseModel):
    entrepreneur_id: UUID4
    user: UserResponse
    company_name: str
    company_registration_number: Optional[str]
    company_description: Optional[str]
    industry_sector: Optional[str]
    founding_date: Optional[date]
    number_of_employees: Optional[int]
    annual_revenue: Optional[float]
    has_raised_funds: Optional[bool]
    amount_raised: Optional[float]
    wants_to_raise_funds: Optional[bool]
    desired_funding_amount: Optional[float]

    # Pièces jointes
    identity_card_url: Optional[HttpUrl]
    company_logo_url: Optional[HttpUrl]
    registration_document_url: Optional[HttpUrl]
    professional_card_url: Optional[HttpUrl]

    # Niveau
    company_not_created: Optional[bool]
    company_recently_created: Optional[bool]
    company_established: Optional[bool]

    validation_status: str
    validation_date: Optional[datetime]
    validated_by: Optional[UUID4]

class EntrepreneurOut(EntrepreneurBase):
    entrepreneur_id: UUID

    class Config:
        from_attributes = True

class EntrepreneurProfileUpdate(BaseModel):
    """Schéma pour mise à jour du profil entrepreneur"""
    # Infos entreprise
    company_name: Optional[str] = None
    company_description: Optional[str] = None
    industry_sector: Optional[str] = None
    company_registration_number: Optional[str] = None
    founding_date: Optional[date] = None
    
    # Données économiques
    number_of_employees: Optional[int] = None
    annual_revenue: Optional[float] = None
    
    # Financement
    has_raised_funds: Optional[bool] = None
    amount_raised: Optional[float] = None
    wants_to_raise_funds: Optional[bool] = None
    desired_funding_amount: Optional[float] = None
    
    # Maturité (un seul peut être True)
    company_not_created: Optional[bool] = None
    company_recently_created: Optional[bool] = None
    company_established: Optional[bool] = None

class EntrepreneurDocumentUpdate(BaseModel):
    """Schéma pour mise à jour des documents"""
    identity_card_url: Optional[str] = None
    company_logo_url: Optional[str] = None
    registration_document_url: Optional[str] = None
    professional_card_url: Optional[str] = None

class EntrepreneurStats(BaseModel):
    """Statistiques entrepreneur"""
    profile_completion: int
    validation_status: str
    company_maturity: str
    programs_joined: int
    assignments_completed: int
    documents_uploaded: int

class EntrepreneurDashboard(BaseModel):
    """Dashboard entrepreneur complet"""
    entrepreneur: EntrepreneurResponse
    stats: EntrepreneurStats
    recent_activities: List[dict] = []
    next_steps: List[str] = []

class EntrepreneurPublicProfile(BaseModel):
    """Profil public entrepreneur (pour listing)"""
    entrepreneur_id: UUID4
    company_name: str
    industry_sector: Optional[str]
    company_maturity: str
    validation_status: str
    company_logo_url: Optional[str]
    founding_date: Optional[date]
    number_of_employees: Optional[int]

class EntrepreneurActivity(BaseModel):
    """Activité récente de l'entrepreneur"""
    activity_type: str  # "enrollment", "completion", "document_upload", "profile_update"
    title: str
    description: str
    date: datetime
    related_id: Optional[str] = None  # ID de l'objet lié (programme, document, etc.)

class EntrepreneurNotification(BaseModel):
    """Notification pour l'entrepreneur"""
    notification_type: str  # "info", "success", "warning", "error"
    title: str
    message: str
    date: datetime
    is_read: bool = False
    action_url: Optional[str] = None

class EntrepreneurQuickActions(BaseModel):
    """Actions rapides suggérées"""
    action_type: str  # "complete_profile", "upload_document", "join_program", "update_info"
    title: str
    description: str
    priority: str  # "high", "medium", "low"
    action_url: str

class EntrepreneurDashboardAdvanced(BaseModel):
    """Dashboard entrepreneur enrichi"""
    # Infos de base
    entrepreneur: EntrepreneurResponse
    stats: EntrepreneurStats
    
    # Programmes
    active_programs: List[ProgramWithParticipation] = []
    recommended_programs: List[ProgramWithParticipation] = []
    
    # Activités et notifications
    recent_activities: List[EntrepreneurActivity] = []
    notifications: List[EntrepreneurNotification] = []
    quick_actions: List[EntrepreneurQuickActions] = []
    
    # Métriques de progression
    profile_completion_details: Dict[str, Any] = {}
    next_milestones: List[str] = []
    
    # Statistiques visuelles
    monthly_progress: Dict[str, int] = {}  # Progression par mois
    achievement_badges: List[str] = []    # Badges obtenus

class EntrepreneurProgressReport(BaseModel):
    """Rapport de progression détaillé"""
    period: str  # "monthly", "quarterly", "yearly"
    start_date: date
    end_date: date
    
    # Métriques clés
    programs_joined: int
    programs_completed: int
    assignments_submitted: int
    skills_acquired: List[str] = []
    
    # Progression
    profile_score_evolution: List[Dict[str, Any]] = []
    engagement_score: float
    recommendation_score: float
    
    # Comparaison
    peer_comparison: Dict[str, float] = {}  # Comparaison avec autres entrepreneurs
