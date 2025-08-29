from sqlalchemy.orm import Session
from app.models.program import Program
from app.models.programParticipant import CompletionStatus, ProgramParticipant
from app.models.entrepreneur import Entrepreneur, ValidationStatus
from app.models.user import User
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import date, datetime

def create_entrepreneur_profile(db: Session, entrepreneur_data: Dict[str, Any]) -> Entrepreneur:
    """Créer un profil entrepreneur (utilisateur déjà créé)"""
    entrepreneur = Entrepreneur(**entrepreneur_data)
    db.add(entrepreneur)
    db.commit()
    db.refresh(entrepreneur)
    return entrepreneur

def get_entrepreneur_by_user_id(db: Session, user_id: UUID) -> Optional[Entrepreneur]:
    return db.query(Entrepreneur).filter(Entrepreneur.user_id == user_id).first()

def get_entrepreneur_by_id(db: Session, entrepreneur_id: UUID) -> Optional[Entrepreneur]:
    return db.query(Entrepreneur).filter(Entrepreneur.entrepreneur_id == entrepreneur_id).first()

def get_entrepreneurs_by_status(db: Session, status: ValidationStatus) -> list[Entrepreneur]:
    """Récupérer entrepreneurs par statut de validation"""
    return db.query(Entrepreneur).filter(Entrepreneur.validation_status == status).all()

def update_entrepreneur_validation(
    db: Session, 
    entrepreneur_id: UUID, 
    status: ValidationStatus, 
    validated_by: UUID
) -> Optional[Entrepreneur]:
    """Valider/rejeter un entrepreneur"""
    entrepreneur = db.query(Entrepreneur).filter(Entrepreneur.entrepreneur_id == entrepreneur_id).first()
    if not entrepreneur:
        return None
    
    entrepreneur.validation_status = status
    entrepreneur.validation_date = datetime.utcnow()
    entrepreneur.validated_by = validated_by
    
    db.commit()
    db.refresh(entrepreneur)
    return entrepreneur

def update_entrepreneur_profile(
    db: Session, 
    entrepreneur_id: UUID, 
    update_data: Dict[str, Any]
) -> Optional[Entrepreneur]:
    """Mettre à jour profil entrepreneur"""
    entrepreneur = db.query(Entrepreneur).filter(Entrepreneur.entrepreneur_id == entrepreneur_id).first()
    if not entrepreneur:
        return None
    
    for field, value in update_data.items():
        if hasattr(entrepreneur, field):
            setattr(entrepreneur, field, value)
    
    db.commit()
    db.refresh(entrepreneur)
    return entrepreneur

def get_entrepreneurs_with_users(db: Session, skip: int = 0, limit: int = 100):
    """Récupérer entrepreneurs avec leurs infos utilisateur"""
    return db.query(Entrepreneur).join(User).offset(skip).limit(limit).all()

def get_entrepreneurs_pending_validation(db: Session) -> List[Entrepreneur]:
    """Récupérer entrepreneurs en attente de validation"""
    return db.query(Entrepreneur).filter(
        Entrepreneur.validation_status == ValidationStatus.pending
    ).all()

def get_entrepreneur_with_user(db: Session, entrepreneur_id: UUID) -> Optional[Entrepreneur]:
    """Récupérer entrepreneur avec ses infos utilisateur"""
    return db.query(Entrepreneur).join(User).filter(
        Entrepreneur.entrepreneur_id == entrepreneur_id
    ).first()

def update_entrepreneur_documents(
    db: Session,
    entrepreneur_id: UUID,
    document_updates: Dict[str, str]
) -> Optional[Entrepreneur]:
    """Mettre à jour les documents d'un entrepreneur"""
    entrepreneur = db.query(Entrepreneur).filter(
        Entrepreneur.entrepreneur_id == entrepreneur_id
    ).first()
    
    if not entrepreneur:
        return None
    
    # Mise à jour des URLs de documents
    document_fields = [
        'identity_card_url', 'company_logo_url', 
        'registration_document_url', 'professional_card_url'
    ]
    
    for field, url in document_updates.items():
        if field in document_fields and hasattr(entrepreneur, field):
            setattr(entrepreneur, field, url)
    
    db.commit()
    db.refresh(entrepreneur)
    return entrepreneur

def get_entrepreneur_stats(db: Session, entrepreneur_id: UUID) -> Dict[str, Any]:
    """Statistiques d'un entrepreneur"""
    entrepreneur = db.query(Entrepreneur).filter(
        Entrepreneur.entrepreneur_id == entrepreneur_id
    ).first()
    
    if not entrepreneur:
        return {}
    
    # TODO: Ajouter les stats réelles quand les autres modèles seront prêts
    stats = {
        "profile_completion": calculate_profile_completion(entrepreneur),
        "validation_status": entrepreneur.validation_status.value,
        "company_maturity": get_company_maturity_level(entrepreneur),
        "programs_joined": 0,  # À implémenter avec ProgramParticipant
        "assignments_completed": 0,  # À implémenter avec AssignmentSubmission
        "documents_uploaded": count_uploaded_documents(entrepreneur)
    }
    
    return stats

def calculate_profile_completion(entrepreneur: Entrepreneur) -> int:
    """Calculer le pourcentage de completion du profil"""
    total_fields = 0
    completed_fields = 0
    
    # Champs obligatoires
    required_fields = [
        'company_name', 'company_description', 'industry_sector'
    ]
    
    # Champs optionnels mais recommandés
    optional_fields = [
        'company_registration_number', 'founding_date', 'number_of_employees',
        'annual_revenue', 'identity_card_url', 'company_logo_url'
    ]
    
    # Vérifier champs obligatoires
    for field in required_fields:
        total_fields += 2  # Poids double pour obligatoires
        if getattr(entrepreneur, field, None):
            completed_fields += 2
    
    # Vérifier champs optionnels
    for field in optional_fields:
        total_fields += 1
        if getattr(entrepreneur, field, None):
            completed_fields += 1
    
    # Vérifier maturité d'entreprise
    total_fields += 2
    if (entrepreneur.company_not_created or 
        entrepreneur.company_recently_created or 
        entrepreneur.company_established):
        completed_fields += 2
    
    return int((completed_fields / total_fields) * 100) if total_fields > 0 else 0

def get_company_maturity_level(entrepreneur: Entrepreneur) -> str:
    """Déterminer le niveau de maturité de l'entreprise"""
    if entrepreneur.company_not_created:
        return "Idée/Projet"
    elif entrepreneur.company_recently_created:
        return "Startup récente"
    elif entrepreneur.company_established:
        return "Entreprise établie"
    else:
        return "Non défini"

def count_uploaded_documents(entrepreneur: Entrepreneur) -> int:
    """Compter les documents uploadés"""
    count = 0
    document_fields = [
        entrepreneur.identity_card_url,
        entrepreneur.company_logo_url,
        entrepreneur.registration_document_url,
        entrepreneur.professional_card_url
    ]
    
    for doc_url in document_fields:
        if doc_url:
            count += 1
    
    return count

def get_entrepreneur_recent_activities(
    db: Session, 
    entrepreneur_id: UUID, 
    limit: int = 10
) -> List[Dict[str, Any]]:
    """Récupérer les activités récentes d'un entrepreneur"""
    activities = []
    
    # Activités de participation aux programmes
    participations = db.query(ProgramParticipant).filter(
        ProgramParticipant.entrepreneur_id == entrepreneur_id
    ).order_by(ProgramParticipant.enrollment_request_date.desc()).limit(5).all()
    
    for participation in participations:
        activities.append({
            "activity_type": "enrollment",
            "title": "Inscription à un programme",
            "description": f"Inscrit au programme: {participation.program.name}",
            "date": participation.enrollment_request_date,
            "related_id": str(participation.program.program_id)
        })
        
        if participation.completion_date:
            activities.append({
                "activity_type": "completion",
                "title": "Programme complété",
                "description": f"Programme complété: {participation.program.name}",
                "date": participation.completion_date,
                "related_id": str(participation.program.program_id)
            })
    
    # Trier par date décroissante et limiter
    activities.sort(key=lambda x: x['date'], reverse=True)
    return activities[:limit]

def get_entrepreneur_notifications(
    db: Session, 
    entrepreneur_id: UUID,
    unread_only: bool = False,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """Récupérer les notifications d'un entrepreneur"""
    # TODO: Implémenter avec le modèle Notification réel
    # Pour l'instant, retourner des notifications mockées
    notifications = []
    
    entrepreneur = get_entrepreneur_by_id(db, entrepreneur_id)
    if not entrepreneur:
        return notifications
    
    # Notifications basées sur le statut
    if entrepreneur.validation_status == ValidationStatus.pending:
        notifications.append({
            "notification_type": "warning",
            "title": "Validation en cours",
            "message": "Votre profil est en cours de validation par notre équipe",
            "date": datetime.utcnow(),
            "is_read": False,
            "action_url": None
        })
    
    # Notifications basées sur la completion du profil
    completion = calculate_profile_completion(entrepreneur)
    if completion < 80:
        notifications.append({
            "notification_type": "info",
            "title": "Profil incomplet",
            "message": f"Votre profil est complété à {completion}%. Complétez-le pour accéder à plus d'opportunités.",
            "date": datetime.utcnow(),
            "is_read": False,
            "action_url": "/entrepreneur/profile"
        })
    
    # Documents manquants
    doc_count = count_uploaded_documents(entrepreneur)
    if doc_count < 2:
        notifications.append({
            "notification_type": "warning",
            "title": "Documents manquants",
            "message": "Uploadez vos documents pour finaliser votre profil",
            "date": datetime.utcnow(),
            "is_read": False,
            "action_url": "/entrepreneur/documents"
        })
    
    return notifications[:limit]

def get_entrepreneur_quick_actions(
    db: Session, 
    entrepreneur_id: UUID
) -> List[Dict[str, Any]]:
    """Actions rapides suggérées pour l'entrepreneur"""
    actions = []
    
    entrepreneur = get_entrepreneur_by_id(db, entrepreneur_id)
    if not entrepreneur:
        return actions
    
    # Action basée sur completion du profil
    completion = calculate_profile_completion(entrepreneur)
    if completion < 100:
        actions.append({
            "action_type": "complete_profile",
            "title": "Compléter mon profil",
            "description": f"Votre profil est à {completion}%. Complétez-le pour plus d'opportunités.",
            "priority": "high" if completion < 60 else "medium",
            "action_url": "/entrepreneur/profile"
        })
    
    # Documents manquants
    doc_count = count_uploaded_documents(entrepreneur)
    if doc_count < 2:
        actions.append({
            "action_type": "upload_document",
            "title": "Uploader mes documents",
            "description": "Ajoutez vos documents d'identité et d'entreprise",
            "priority": "high",
            "action_url": "/entrepreneur/documents"
        })
    
    # Logo manquant
    if not entrepreneur.company_logo_url:
        actions.append({
            "action_type": "upload_logo",
            "title": "Ajouter le logo de mon entreprise",
            "description": "Personnalisez votre profil avec le logo de votre entreprise",
            "priority": "medium",
            "action_url": "/entrepreneur/logo"
        })
    
    # Rejoindre un programme si validé
    if entrepreneur.validation_status == ValidationStatus.approved:
        # Vérifier s'il a des programmes actifs
        active_participations = db.query(ProgramParticipant).filter(
            ProgramParticipant.entrepreneur_id == entrepreneur_id,
            ProgramParticipant.completion_status == CompletionStatus.in_progress
        ).count()
        
        if active_participations == 0:
            actions.append({
                "action_type": "join_program",
                "title": "Rejoindre un programme",
                "description": "Explorez nos programmes d'accélération",
                "priority": "high",
                "action_url": "/programs"
            })
    
    return actions

def get_entrepreneur_recommended_programs(
    db: Session, 
    entrepreneur_id: UUID,
    limit: int = 3
) -> List[Program]:
    """Programmes recommandés pour un entrepreneur"""
    entrepreneur = get_entrepreneur_by_id(db, entrepreneur_id)
    if not entrepreneur:
        return []
    
    # Récupérer programmes auxquels il n'est pas inscrit
    enrolled_program_ids = db.query(ProgramParticipant.program_id).filter(
        ProgramParticipant.entrepreneur_id == entrepreneur_id
    ).subquery()
    
    recommended = db.query(Program).filter(
        Program.is_active == True,
        Program.end_date >= date.today(),
        ~Program.program_id.in_(enrolled_program_ids)
    ).limit(limit).all()
    
    return recommended

def get_entrepreneur_achievement_badges(
    db: Session, 
    entrepreneur_id: UUID
) -> List[str]:
    """Badges obtenus par l'entrepreneur"""
    badges = []
    
    entrepreneur = get_entrepreneur_by_id(db, entrepreneur_id)
    if not entrepreneur:
        return badges
    
    # Badge profil complet
    completion = calculate_profile_completion(entrepreneur)
    if completion >= 100:
        badges.append("Profil Complet")
    elif completion >= 80:
        badges.append("Profil Avancé")
    
    # Badge documents
    doc_count = count_uploaded_documents(entrepreneur)
    if doc_count >= 3:
        badges.append("Bien Documenté")
    
    # Badge validation
    if entrepreneur.validation_status == ValidationStatus.approved:
        badges.append("Entrepreneur Validé")
    
    # Badge programmes (nécessite les participations)
    completed_programs = db.query(ProgramParticipant).filter(
        ProgramParticipant.entrepreneur_id == entrepreneur_id,
        ProgramParticipant.completion_status == CompletionStatus.completed
    ).count()
    
    if completed_programs >= 3:
        badges.append("Expert en Formation")
    elif completed_programs >= 1:
        badges.append("Premier Pas")
    
    return badges

def calculate_entrepreneur_engagement_score(
    db: Session, 
    entrepreneur_id: UUID
) -> float:
    """Calculer le score d'engagement de l'entrepreneur"""
    score = 0.0
    
    entrepreneur = get_entrepreneur_by_id(db, entrepreneur_id)
    if not entrepreneur:
        return score
    
    # Score basé sur completion du profil (40 points max)
    completion = calculate_profile_completion(entrepreneur)
    score += (completion / 100) * 40
    
    # Score basé sur programmes (40 points max)
    participations = db.query(ProgramParticipant).filter(
        ProgramParticipant.entrepreneur_id == entrepreneur_id
    ).all()
    
    active_programs = len([p for p in participations if p.completion_status == CompletionStatus.in_progress])
    completed_programs = len([p for p in participations if p.completion_status == CompletionStatus.completed])
    
    score += min(active_programs * 10, 20)  # Max 20 points pour programmes actifs
    score += min(completed_programs * 10, 20)  # Max 20 points pour programmes complétés
    
    # Score basé sur documents (20 points max)
    doc_count = count_uploaded_documents(entrepreneur)
    score += min(doc_count * 5, 20)
    
    return min(score, 100.0)  # Max 100 points