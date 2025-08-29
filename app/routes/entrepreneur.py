from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from uuid import UUID

from app.crud.program import get_entrepreneur_programs
from app.database import get_db
from app.auth.dependencies import get_current_user, require_entrepreneur
from app.models.user import User
from app.models.entrepreneur import Entrepreneur
from app.schemas.entrepreneur import (
    EntrepreneurActivity, EntrepreneurDashboardAdvanced, EntrepreneurNotification, EntrepreneurProgressReport, EntrepreneurQuickActions, EntrepreneurResponse, EntrepreneurProfileUpdate, EntrepreneurDocumentUpdate,
    EntrepreneurStats, EntrepreneurDashboard, EntrepreneurPublicProfile
)
from app.crud.entrepreneur import (
    calculate_entrepreneur_engagement_score, get_company_maturity_level, get_entrepreneur_achievement_badges, get_entrepreneur_by_user_id, get_entrepreneur_notifications, get_entrepreneur_quick_actions, get_entrepreneur_recent_activities, get_entrepreneur_recommended_programs, update_entrepreneur_profile,
    update_entrepreneur_documents, get_entrepreneur_stats,
    calculate_profile_completion, get_entrepreneurs_with_users
)
from app.crud.user import update_user
from app.utils.email import send_entrepreneur_registration_confirmation

router = APIRouter(prefix="/entrepreneur", tags=["Entrepreneur"])

@router.get("/me", response_model=EntrepreneurResponse)
def get_my_profile(
    current_user: User = Depends(require_entrepreneur),
    db: Session = Depends(get_db)
):
    """📋 Récupérer mon profil entrepreneur"""
    entrepreneur = get_entrepreneur_by_user_id(db, current_user.user_id)
    
    if not entrepreneur:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil entrepreneur non trouvé"
        )
    
    return entrepreneur

@router.put("/me", response_model=EntrepreneurResponse)
def update_my_profile(
    profile_data: EntrepreneurProfileUpdate,
    current_user: User = Depends(require_entrepreneur),
    db: Session = Depends(get_db)
):
    """✏️ Mettre à jour mon profil entrepreneur"""
    entrepreneur = get_entrepreneur_by_user_id(db, current_user.user_id)
    
    if not entrepreneur:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil entrepreneur non trouvé"
        )
    
    # Validation de la maturité d'entreprise (un seul peut être True)
    maturity_fields = [
        profile_data.company_not_created,
        profile_data.company_recently_created, 
        profile_data.company_established
    ]
    
    true_count = sum(1 for field in maturity_fields if field is True)
    if true_count > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un seul niveau de maturité d'entreprise peut être sélectionné"
        )
    
    # Mise à jour
    update_data = profile_data.dict(exclude_unset=True)
    updated_entrepreneur = update_entrepreneur_profile(
        db, entrepreneur.entrepreneur_id, update_data
    )
    
    return updated_entrepreneur

@router.put("/me/documents", response_model=EntrepreneurResponse)
def update_my_documents(
    documents: EntrepreneurDocumentUpdate,
    current_user: User = Depends(require_entrepreneur),
    db: Session = Depends(get_db)
):
    """📎 Mettre à jour mes documents"""
    entrepreneur = get_entrepreneur_by_user_id(db, current_user.user_id)
    
    if not entrepreneur:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil entrepreneur non trouvé"
        )
    
    document_updates = documents.dict(exclude_unset=True)
    updated_entrepreneur = update_entrepreneur_documents(
        db, entrepreneur.entrepreneur_id, document_updates
    )
    
    return updated_entrepreneur

@router.get("/me/stats", response_model=EntrepreneurStats)
def get_my_stats(
    current_user: User = Depends(require_entrepreneur),
    db: Session = Depends(get_db)
):
    """📊 Récupérer mes statistiques"""
    entrepreneur = get_entrepreneur_by_user_id(db, current_user.user_id)
    
    if not entrepreneur:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil entrepreneur non trouvé"
        )
    
    stats = get_entrepreneur_stats(db, entrepreneur.entrepreneur_id)
    return EntrepreneurStats(**stats)


@router.get("/directory", response_model=List[EntrepreneurPublicProfile])
def get_entrepreneur_directory(
    skip: int = 0,
    limit: int = 20,
    industry: str = None,
    maturity: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """📋 Annuaire public des entrepreneurs (validés uniquement)"""
    # TODO: Implémenter filtres et requête optimisée
    entrepreneurs = get_entrepreneurs_with_users(db, skip, limit)
    
    # Filtrer uniquement les validés
    validated_entrepreneurs = [
        e for e in entrepreneurs 
        if e.validation_status.value == "approved"
    ]
    
    # Convertir en profils publics
    public_profiles = []
    for entrepreneur in validated_entrepreneurs:
        public_profiles.append(EntrepreneurPublicProfile(
            entrepreneur_id=entrepreneur.entrepreneur_id,
            company_name=entrepreneur.company_name,
            industry_sector=entrepreneur.industry_sector,
            company_maturity=get_company_maturity_level(entrepreneur),
            validation_status=entrepreneur.validation_status.value,
            company_logo_url=entrepreneur.company_logo_url,
            founding_date=entrepreneur.founding_date,
            number_of_employees=entrepreneur.number_of_employees
        ))
    
    return public_profiles

def generate_next_steps(entrepreneur: Entrepreneur, stats: Dict[str, Any]) -> List[str]:
    """Générer les prochaines étapes recommandées"""
    steps = []
    
    # Profil incomplet
    if stats['profile_completion'] < 80:
        steps.append("Compléter votre profil entrepreneur")
    
    # Documents manquants
    if stats['documents_uploaded'] < 2:
        steps.append("Uploader vos documents (carte d'identité, documents entreprise)")
    
    # Validation en attente
    if stats['validation_status'] == 'pending':
        steps.append("Attendre la validation de votre profil par l'équipe NUKU")
    
    # Logo manquant
    if not entrepreneur.company_logo_url:
        steps.append("Ajouter le logo de votre entreprise")
    
    # Niveau de maturité non défini
    if stats['company_maturity'] == 'Non défini':
        steps.append("Définir le niveau de maturité de votre entreprise")
    
    # Programmes
    if stats['programs_joined'] == 0 and stats['validation_status'] == 'approved':
        steps.append("Explorer les programmes d'accélération disponibles")
    
    return steps[:5]  # Max 5 étapes

@router.get("/me/dashboard", response_model=EntrepreneurDashboardAdvanced)
def get_my_dashboard(
    current_user: User = Depends(require_entrepreneur),
    db: Session = Depends(get_db)
):
    """🏠 Dashboard entrepreneur complet"""
    entrepreneur = get_entrepreneur_by_user_id(db, current_user.user_id)
    
    if not entrepreneur:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil entrepreneur non trouvé"
        )
    
    # Récupérer toutes les données
    stats = get_entrepreneur_stats(db, entrepreneur.entrepreneur_id)
    
    # Programmes actifs
    from app.crud.program import get_entrepreneur_programs, get_program
    participations = get_entrepreneur_programs(db, entrepreneur.entrepreneur_id)
    active_programs = []
    
    for participation in participations:
        if participation.completion_status.value == "in_progress":
            program = get_program(db, participation.program_id)
            if program:
                from app.schemas.program import ProgramWithParticipation
                program_data = ProgramWithParticipation(
                    **program.__dict__,
                    is_enrolled=True,
                    enrollment_request_date=participation.enrollment_request_date,
                    completion_status=participation.completion_status,
                    participants_count=0,  # Peut être optimisé
                    available_spots=None
                )
                active_programs.append(program_data)
    
    # Programmes recommandés
    recommended_programs_data = get_entrepreneur_recommended_programs(
        db, entrepreneur.entrepreneur_id
    )
    recommended_programs = []
    for program in recommended_programs_data:
        from app.schemas.program import ProgramWithParticipation
        program_data = ProgramWithParticipation(
            **program.__dict__,
            is_enrolled=False,
            participants_count=0,
            available_spots=None
        )
        recommended_programs.append(program_data)
    
    # Activités récentes
    activities_data = get_entrepreneur_recent_activities(db, entrepreneur.entrepreneur_id)
    recent_activities = [EntrepreneurActivity(**activity) for activity in activities_data]
    
    # Notifications
    notifications_data = get_entrepreneur_notifications(db, entrepreneur.entrepreneur_id)
    notifications = [EntrepreneurNotification(**notif) for notif in notifications_data]
    
    # Actions rapides
    actions_data = get_entrepreneur_quick_actions(db, entrepreneur.entrepreneur_id)
    quick_actions = [EntrepreneurQuickActions(**action) for action in actions_data]
    
    # Détails de completion du profil
    completion = calculate_profile_completion(entrepreneur)
    profile_completion_details = {
        "overall_percentage": completion,
        "missing_fields": [],
        "completed_sections": [],
        "priority_actions": []
    }
    
    if completion < 100:
        if not entrepreneur.company_description:
            profile_completion_details["missing_fields"].append("Description de l'entreprise")
        if not entrepreneur.industry_sector:
            profile_completion_details["missing_fields"].append("Secteur d'activité")
        if not entrepreneur.company_logo_url:
            profile_completion_details["missing_fields"].append("Logo de l'entreprise")
    
    # Badges obtenus
    achievement_badges = get_entrepreneur_achievement_badges(db, entrepreneur.entrepreneur_id)
    
    # Score d'engagement
    engagement_score = calculate_entrepreneur_engagement_score(db, entrepreneur.entrepreneur_id)
    
    # Prochaines étapes
    next_milestones = generate_next_steps(entrepreneur, stats)
    
    # Progression mensuelle (données mockées pour l'instant)
    monthly_progress = {
        "janvier": 20,
        "février": 35,
        "mars": 50,
        "avril": 65,
        "mai": 80
    }
    
    return EntrepreneurDashboardAdvanced(
        entrepreneur=entrepreneur,
        stats=EntrepreneurStats(**stats),
        active_programs=active_programs,
        recommended_programs=recommended_programs,
        recent_activities=recent_activities,
        notifications=notifications,
        quick_actions=quick_actions,
        profile_completion_details=profile_completion_details,
        next_milestones=next_milestones,
        monthly_progress=monthly_progress,
        achievement_badges=achievement_badges
    )

# Nouvelles routes additionnelles

@router.get("/me/notifications", response_model=List[EntrepreneurNotification])
def get_my_notifications(
    unread_only: bool = Query(False, description="Afficher seulement les non lues"),
    limit: int = Query(20, description="Nombre maximum de notifications"),
    current_user: User = Depends(require_entrepreneur),
    db: Session = Depends(get_db)
):
    """🔔 Mes notifications"""
    entrepreneur = get_entrepreneur_by_user_id(db, current_user.user_id)
    
    if not entrepreneur:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil entrepreneur non trouvé"
        )
    
    notifications_data = get_entrepreneur_notifications(
        db, entrepreneur.entrepreneur_id, unread_only, limit
    )
    
    return [EntrepreneurNotification(**notif) for notif in notifications_data]

@router.get("/me/activities", response_model=List[EntrepreneurActivity])
def get_my_activities(
    limit: int = Query(20, description="Nombre maximum d'activités"),
    current_user: User = Depends(require_entrepreneur),
    db: Session = Depends(get_db)
):
    """📋 Mes activités récentes"""
    entrepreneur = get_entrepreneur_by_user_id(db, current_user.user_id)
    
    if not entrepreneur:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil entrepreneur non trouvé"
        )
    
    activities_data = get_entrepreneur_recent_activities(
        db, entrepreneur.entrepreneur_id, limit
    )
    
    return [EntrepreneurActivity(**activity) for activity in activities_data]

@router.get("/me/progress-report", response_model=EntrepreneurProgressReport)
def get_my_progress_report(
    period: str = Query("monthly", description="Période du rapport"),
    current_user: User = Depends(require_entrepreneur),
    db: Session = Depends(get_db)
):
    """📈 Rapport de progression"""
    entrepreneur = get_entrepreneur_by_user_id(db, current_user.user_id)
    
    if not entrepreneur:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil entrepreneur non trouvé"
        )
    
    # Calculer dates selon la période
    end_date = date.today()
    if period == "monthly":
        start_date = date(end_date.year, end_date.month, 1)
    elif period == "quarterly":
        quarter = (end_date.month - 1) // 3 + 1
        start_date = date(end_date.year, (quarter - 1) * 3 + 1, 1)
    else:  # yearly
        start_date = date(end_date.year, 1, 1)
    
    # Récupérer données de progression
    participations = get_entrepreneur_programs(db, entrepreneur.entrepreneur_id)
    
    programs_joined = len([
        p for p in participations 
        if p.enrollment_request_date.date() >= start_date
    ])
    
    programs_completed = len([
        p for p in participations 
        if p.completion_date and p.completion_date.date() >= start_date
    ])
    
    # Score d'engagement
    engagement_score = calculate_entrepreneur_engagement_score(db, entrepreneur.entrepreneur_id)
    
    return EntrepreneurProgressReport(
        period=period,
        start_date=start_date,
        end_date=end_date,
        programs_joined=programs_joined,
        programs_completed=programs_completed,
        assignments_submitted=0,  # À implémenter avec AssignmentSubmission
        skills_acquired=[],  # À implémenter
        profile_score_evolution=[],  # À implémenter
        engagement_score=engagement_score,
        recommendation_score=85.0,  # Mockée
        peer_comparison={"moyenne_secteur": 75.0, "top_10_percent": 90.0}  # Mockée
    )