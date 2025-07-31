from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from uuid import UUID, uuid4
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from app.models.expert import Expert
from app.models.user import User, UserType, UserStatus
from app.models.program import Program
from app.models.programParticipant import ProgramParticipant
from app.schemas.expert import ExpertCreate, ExpertUpdate
from app.utils.security import hash_password, generate_temporary_password
from app.utils.url_to_str import optional_str
from app.utils.uuid import uuid_column

def create_expert(db: Session, data: ExpertCreate, temp_password: str) -> Expert:
    """Créer un expert avec utilisateur associé"""
    # Créer utilisateur
    user = User(
        user_id=uuid4(),
        first_name=data.user.first_name,
        last_name=data.user.last_name,
        email=data.user.email,
        phone=data.user.phone,
        password_hash=hash_password(temp_password),
        user_type=UserType.expert,
        status=UserStatus.active,
    )
    db.add(user)
    db.flush()  # Pour avoir l'user_id
    
    # Créer expert
    expert = Expert(
        user_id=user.user_id,
        specialization=data.specialization,
        years_of_experience=data.years_of_experience,
        linkedin_profile=optional_str(data.linkedin_profile),
        cv_url=optional_str(data.cv_url),
        bio=data.bio,
        hourly_rate=data.hourly_rate,
        is_active=data.is_active
    )
    db.add(expert)
    db.commit()
    db.refresh(expert)
    return expert

def get_expert_by_user_id(db: Session, user_id: UUID) -> Optional[Expert]:
    """Récupérer expert par user_id"""
    return db.query(Expert).filter(Expert.user_id == user_id).first()

def get_expert_by_id(db: Session, expert_id: UUID) -> Optional[Expert]:
    """Récupérer expert par expert_id"""
    return db.query(Expert).filter(Expert.expert_id == expert_id).first()

def get_all_experts(db: Session, active_only: bool = True) -> List[Expert]:
    """Récupérer tous les experts"""
    query = db.query(Expert)
    if active_only:
        query = query.filter(Expert.is_active == True)
    return query.all()

def update_expert_profile(
    db: Session, 
    expert_id: UUID, 
    update_data: Dict[str, Any]
) -> Optional[Expert]:
    """Mettre à jour profil expert"""
    expert = db.query(Expert).filter(Expert.expert_id == expert_id).first()
    if not expert:
        return None
    
    for field, value in update_data.items():
        if hasattr(expert, field):
            setattr(expert, field, value)
    
    db.commit()
    db.refresh(expert)
    return expert

# Remplacez ces fonctions dans votre fichier app/crud/expert.py

def get_expert_programs(db: Session, expert_id: UUID) -> List[Dict[str, Any]]:
    """Programmes assignés à un expert"""
    from app.crud.programExpert import get_expert_programs_with_details
    return get_expert_programs_with_details(db, expert_id)

def get_expert_entrepreneurs(db: Session, expert_id: UUID) -> List[Dict[str, Any]]:
    """Entrepreneurs accompagnés par un expert"""
    from app.crud.programExpert import get_expert_entrepreneurs_in_programs
    return get_expert_entrepreneurs_in_programs(db, expert_id)

def get_expert_stats(db: Session, expert_id: UUID) -> Dict[str, Any]:
    """Statistiques d'un expert (version complète)"""
    expert = get_expert_by_id(db, expert_id)
    if not expert:
        return {}
    
    # Récupérer programmes assignés
    programs = get_expert_programs(db, expert_id)
    active_programs = [p for p in programs if p.get('is_active', False)]
    
    # Récupérer entrepreneurs accompagnés
    entrepreneurs = get_expert_entrepreneurs(db, expert_id)
    
    # TODO: Compter modules et assignments créés quand ces modèles seront implémentés
    modules_created = 0
    assignments_created = 0
    total_sessions = 0
    this_month_sessions = 0
    this_week_sessions = 0
    
    stats = {
        "profile_completion": calculate_expert_profile_completion(expert),
        "is_active": expert.is_active,
        "specialization": expert.specialization,
        "years_of_experience": expert.years_of_experience or 0,
        
        # Stats d'activité réelles
        "programs_assigned": len(programs),
        "active_programs": len(active_programs),
        "entrepreneurs_mentored": len(entrepreneurs),
        "modules_created": modules_created,
        "assignments_created": assignments_created,
        "total_sessions": total_sessions,
        "average_rating": 4.5,  # Mockée pour l'instant
        
        # Stats temporelles
        "this_month_sessions": this_month_sessions,
        "this_week_sessions": this_week_sessions,
    }
    
    return stats

def get_expert_recent_activities(
    db: Session, 
    expert_id: UUID, 
    limit: int = 10
) -> List[Dict[str, Any]]:
    """Activités récentes de l'expert (version réelle)"""
    activities = []
    
    expert = get_expert_by_id(db, expert_id)
    if not expert:
        return activities
    
    # Activités d'assignment aux programmes
    from app.crud.programExpert import get_expert_programs
    assignments = get_expert_programs(db, expert_id)
    
    for assignment in assignments:
        activities.append({
            "activity_type": "program_assignment",
            "title": f"Assigné au programme {assignment.get('program_name', 'N/A')}",
            "description": f"Rôle: {assignment.get('role', 'N/A')}",
            "date": assignment.get('assigned_at', datetime.utcnow()),
            "related_id": assignment.get('program_id')
        })
    
    # Trier par date décroissante
    activities.sort(key=lambda x: x['date'], reverse=True)
    return activities[:limit]

def calculate_expert_profile_completion(expert: Expert) -> int:
    """Calculer le pourcentage de completion du profil expert"""
    total_fields = 0
    completed_fields = 0
    
    # Champs obligatoires
    required_fields = ['specialization']
    
    # Champs recommandés
    recommended_fields = [
        'years_of_experience', 'bio', 'linkedin_profile', 'cv_url', 'hourly_rate'
    ]
    
    # Vérifier champs obligatoires (poids double)
    for field in required_fields:
        total_fields += 2
        if getattr(expert, field, None):
            completed_fields += 2
    
    # Vérifier champs recommandés
    for field in recommended_fields:
        total_fields += 1
        value = getattr(expert, field, None)
        if value is not None and value != "":
            completed_fields += 1
    
    return int((completed_fields / total_fields) * 100) if total_fields > 0 else 0


def search_experts_by_specialization(
    db: Session, 
    specialization: str, 
    active_only: bool = True
) -> List[Expert]:
    """Rechercher experts par spécialisation"""
    query = db.query(Expert).filter(
        Expert.specialization.ilike(f"%{specialization}%")
    )
    
    if active_only:
        query = query.filter(Expert.is_active == True)
    
    return query.all()

def toggle_expert_status(db: Session, expert_id: UUID) -> Optional[Expert]:
    """Activer/Désactiver un expert"""
    expert = get_expert_by_id(db, expert_id)
    if not expert:
        return None
    
    expert.is_active = not expert.is_active
    db.commit()
    db.refresh(expert)
    return expert

def get_experts_leaderboard(db: Session, limit: int = 10) -> List[Dict[str, Any]]:
    """Classement des experts (par performance)"""
    experts = get_all_experts(db, active_only=True)
    
    # TODO: Implémenter vraie logique de classement
    # Pour l'instant, trier par années d'expérience
    leaderboard = []
    
    for expert in experts[:limit]:
        score = (expert.years_of_experience or 0) * 10  # Score simple
        leaderboard.append({
            "expert_id": str(expert.expert_id),
            "name": f"{expert.user.first_name} {expert.user.last_name}",
            "specialization": expert.specialization,
            "score": score,
            "years_experience": expert.years_of_experience or 0,
            "programs_count": 0,  # À implémenter
            "rating": 0.0  # À implémenter
        })
    
    # Trier par score décroissant
    leaderboard.sort(key=lambda x: x['score'], reverse=True)
    return leaderboard