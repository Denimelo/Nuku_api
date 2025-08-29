from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.auth.dependencies import get_current_user, require_expert, require_admin
from app.models.user import User
from app.schemas.expert import (
    ExpertResponse, ExpertProfileUpdate, ExpertStats, ExpertDashboard,
    ExpertActivity, ExpertNotification, ExpertQuickAction, ExpertProgram,
    ExpertEntrepreneur, ExpertPublicProfile, ExpertLeaderboardEntry
)
from app.crud.expert import (
    get_expert_by_user_id, update_expert_profile, get_expert_stats,
    get_expert_recent_activities, get_all_experts, search_experts_by_specialization,
    get_experts_leaderboard, toggle_expert_status
)
from app.crud.programExpert import (
    assign_expert_to_program, remove_expert_from_program, 
    update_expert_role_in_program
)

router = APIRouter(prefix="/expert", tags=["Expert"])

# ========== ROUTES EXPERT (AUTHENTIFIÉ) ==========

@router.get("/me", response_model=ExpertResponse)
def get_my_expert_profile(
    current_user: User = Depends(require_expert),
    db: Session = Depends(get_db)
):
    """👨‍🏫 Mon profil expert"""
    expert = get_expert_by_user_id(db, current_user.user_id)
    
    if not expert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil expert non trouvé"
        )
    
    return expert

@router.put("/me", response_model=ExpertResponse)
def update_my_expert_profile(
    profile_data: ExpertProfileUpdate,
    current_user: User = Depends(require_expert),
    db: Session = Depends(get_db)
):
    """✏️ Mettre à jour mon profil expert"""
    expert = get_expert_by_user_id(db, current_user.user_id)
    
    if not expert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil expert non trouvé"
        )
    
    update_data = profile_data.dict(exclude_unset=True)
    updated_expert = update_expert_profile(db, expert.expert_id, update_data)
    
    return updated_expert

@router.get("/me/stats", response_model=ExpertStats)
def get_my_expert_stats(
    current_user: User = Depends(require_expert),
    db: Session = Depends(get_db)
):
    """📊 Mes statistiques expert"""
    expert = get_expert_by_user_id(db, current_user.user_id)
    
    if not expert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil expert non trouvé"
        )
    
    stats = get_expert_stats(db, expert.expert_id)
    return ExpertStats(**stats)

@router.get("/me/dashboard", response_model=ExpertDashboard)
def get_my_expert_dashboard(
    current_user: User = Depends(require_expert),
    db: Session = Depends(get_db)
):
    """🏠 Dashboard expert complet"""
    expert = get_expert_by_user_id(db, current_user.user_id)
    
    if not expert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil expert non trouvé"
        )
    
    # Récupérer stats
    stats = get_expert_stats(db, expert.expert_id)
    
    # Programmes assignés
    from app.crud.expert import get_expert_programs
    programs_data = get_expert_programs(db, expert.expert_id)
    assigned_programs = [
        ExpertProgram(
            program_id=UUID(p['program_id']),
            program_name=p['program_name'],
            participants_count=p['participants_count'],
            start_date=p['start_date'],
            end_date=p['end_date'],
            is_active=p['is_active'],
            role=p['role']
        ) for p in programs_data
    ]
    
    # Entrepreneurs accompagnés
    from app.crud.expert import get_expert_entrepreneurs
    entrepreneurs_data = get_expert_entrepreneurs(db, expert.expert_id)
    mentored_entrepreneurs = [
        ExpertEntrepreneur(
            entrepreneur_id=UUID(e['entrepreneur_id']),
            entrepreneur_name=e['entrepreneur_name'],
            company_name=e['company_name'],
            industry_sector=e.get('industry_sector'),
            enrollment_request_date=e['enrollment_request_date'],
            progress_percentage=75.0,  # TODO: Calculer vraie progression
            last_interaction=None  # TODO: Implémenter
        ) for e in entrepreneurs_data
    ]
    
    # Activités récentes
    activities_data = get_expert_recent_activities(db, expert.expert_id)
    recent_activities = [ExpertActivity(**activity) for activity in activities_data]
    
    # Notifications (mockées pour l'instant)
    notifications = []
    if stats['profile_completion'] < 80:
        notifications.append(ExpertNotification(
            notification_type="warning",
            title="Profil incomplet",
            message=f"Votre profil est complété à {stats['profile_completion']}%",
            date=datetime.utcnow(),
            action_url="/expert/profile"
        ))
    
    # Actions rapides
    quick_actions = []
    if stats['profile_completion'] < 100:
        quick_actions.append(ExpertQuickAction(
            action_type="complete_profile",
            title="Compléter mon profil",
            description="Améliorez votre visibilité en complétant votre profil",
            priority="high",
            action_url="/expert/profile"
        ))
    
    if stats['modules_created'] == 0:
        quick_actions.append(ExpertQuickAction(
            action_type="create_module",
            title="Créer mon premier module",
            description="Commencez à créer du contenu pédagogique",
            priority="medium",
            action_url="/expert/modules/create"
        ))
    
    # Performance mensuelle (mockée)
    monthly_performance = {
        "sessions_this_month": stats['this_month_sessions'],
        "entrepreneurs_engaged": len(mentored_entrepreneurs),
        "completion_rate": 85.0,
        "satisfaction_score": 4.5
    }
    
    return ExpertDashboard(
        expert=expert,
        stats=ExpertStats(**stats),
        assigned_programs=assigned_programs,
        mentored_entrepreneurs=mentored_entrepreneurs,
        recent_activities=recent_activities,
        notifications=notifications,
        quick_actions=quick_actions,
        monthly_performance=monthly_performance,
        upcoming_sessions=[]  # TODO: Implémenter avec Call model
    )

@router.get("/me/programs", response_model=List[ExpertProgram])
def get_my_expert_programs(
    current_user: User = Depends(require_expert),
    db: Session = Depends(get_db)
):
    """📚 Mes programmes assignés"""
    expert = get_expert_by_user_id(db, current_user.user_id)
    
    if not expert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil expert non trouvé"
        )
    
    from app.crud.expert import get_expert_programs
    programs_data = get_expert_programs(db, expert.expert_id)
    
    return [
        ExpertProgram(
            program_id=UUID(p['program_id']),
            program_name=p['program_name'],
            participants_count=p['participants_count'],
            start_date=p['start_date'],
            end_date=p['end_date'],
            is_active=p['is_active'],
            role=p['role']
        ) for p in programs_data
    ]

@router.get("/me/entrepreneurs", response_model=List[ExpertEntrepreneur])
def get_my_mentored_entrepreneurs(
    current_user: User = Depends(require_expert),
    db: Session = Depends(get_db)
):
    """👥 Entrepreneurs que j'accompagne"""
    expert = get_expert_by_user_id(db, current_user.user_id)
    
    if not expert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil expert non trouvé"
        )
    
    from app.crud.expert import get_expert_entrepreneurs
    entrepreneurs_data = get_expert_entrepreneurs(db, expert.expert_id)
    
    return [
        ExpertEntrepreneur(
            entrepreneur_id=UUID(e['entrepreneur_id']),
            entrepreneur_name=e['entrepreneur_name'],
            company_name=e['company_name'],
            industry_sector=e.get('industry_sector'),
            enrollment_request_date=e['enrollment_request_date'],
            progress_percentage=75.0,  # TODO: Calculer vraie progression
            last_interaction=None  # TODO: Implémenter
        ) for e in entrepreneurs_data
    ]

# ========== ROUTES PUBLIQUES ==========

@router.get("/directory", response_model=List[ExpertPublicProfile])
def get_experts_directory(
    specialization: Optional[str] = Query(None, description="Filtrer par spécialisation"),
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """📋 Annuaire public des experts"""
    
    if specialization:
        experts = search_experts_by_specialization(db, specialization, active_only=True)
    else:
        experts = get_all_experts(db, active_only=True)
    
    # Convertir en profils publics
    public_profiles = []
    for expert in experts[skip:skip+limit]:
        public_profiles.append(ExpertPublicProfile(
            expert_id=expert.expert_id,
            name=f"{expert.user.first_name} {expert.user.last_name}",
            specialization=expert.specialization,
            years_of_experience=expert.years_of_experience,
            bio=expert.bio,
            average_rating=4.5,  # TODO: Calculer vraie note
            total_sessions=25,  # TODO: Compter vraies sessions
            linkedin_profile=expert.linkedin_profile,
            is_available=expert.is_active
        ))
    
    return public_profiles

@router.get("/leaderboard", response_model=List[ExpertLeaderboardEntry])
def get_experts_leaderboard(
    limit: int = Query(10, description="Nombre d'experts dans le classement"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """🏆 Classement des experts"""
    
    leaderboard_data = get_experts_leaderboard(db, limit)
    
    return [
        ExpertLeaderboardEntry(
            expert_id=UUID(entry['expert_id']),
            name=entry['name'],
            specialization=entry['specialization'],
            score=entry['score'],
            years_experience=entry['years_experience'],
            programs_count=entry['programs_count'],
            rating=entry['rating'],
            rank=idx + 1
        ) for idx, entry in enumerate(leaderboard_data)
    ]

# ========== ROUTES ADMIN ==========

@router.post("/assign-to-program")
def assign_expert_to_program_route(
    program_id: UUID,
    expert_id: UUID,
    role: str = "mentor",
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """➕ Assigner expert à programme (Admin)"""
    
    assignment = assign_expert_to_program(
        db, program_id, expert_id, role, current_user.user_id
    )
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Expert déjà assigné à ce programme"
        )
    
    return {"message": "Expert assigné avec succès", "assignment_id": str(assignment.program_expert_id)}

@router.delete("/remove-from-program")
def remove_expert_from_program_route(
    program_id: UUID,
    expert_id: UUID,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """➖ Retirer expert d'un programme (Admin)"""
    
    success = remove_expert_from_program(db, program_id, expert_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment non trouvé"
        )
    
    return {"message": "Expert retiré du programme avec succès"}

@router.put("/{expert_id}/toggle-status")
def toggle_expert_status_route(
    expert_id: UUID,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """🔄 Activer/Désactiver expert (Admin)"""
    
    expert = toggle_expert_status(db, expert_id)
    
    if not expert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expert non trouvé"
        )
    
    status_text = "activé" if expert.is_active else "désactivé"
    return {"message": f"Expert {status_text} avec succès"}