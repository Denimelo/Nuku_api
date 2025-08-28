from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.database import get_db
from app.auth.dependencies import get_current_user, require_admin, require_entrepreneur
from app.models.user import User
from app.models.program import Program
from app.models.entrepreneur import Entrepreneur, ValidationStatus
from app.models.programParticipant import EnrollmentStatus, CompletionStatus
from app.models.module import Module, ModuleStatus
from app.models.moduleProgress import ModuleProgress
from app.schemas.program import EntrepreneurProgramSummary, ProgramCreate, ProgramParticipantResponse, ProgramResponse, ProgramStats, ProgramUpdate, ProgramWithParticipation
from app.crud.program import (
    get_all_programs, get_active_programs, create_program, get_program,
    update_program, delete_program, enroll_entrepreneur_to_program,
    get_entrepreneur_programs, get_program_participants, get_program_participants_count,
    leave_program, get_participation_by_ids, update_participation_status
)
from app.crud.program import (
    get_all_programs, get_active_programs, create_program, get_program,
    update_program, delete_program, enroll_entrepreneur_to_program,
    get_entrepreneur_programs, get_program_participants, get_program_participants_count,
    leave_program, get_participation_by_ids, update_participation_status
)
from app.crud.entrepreneur import get_entrepreneur_by_user_id
from app.models.programParticipant import ProgramParticipant
from app.models.programExpert import ProgramExpert
from app.models.expert import Expert
from app.crud.expert import get_expert

router = APIRouter(prefix="/programs", tags=["Programs"])

# ========== ROUTES PUBLIQUES ==========
@router.post("/{program_id}/enroll")
def request_program_enrollment(
    program_id: UUID,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Demander une inscription à un programme"""
    
    # Vérifier que l'utilisateur est un entrepreneur
    if current_user.user_type.value != "entrepreneur":
        raise HTTPException(status_code=403, detail="Seuls les entrepreneurs peuvent s'inscrire aux programmes")
    
    # Récupérer l'entrepreneur
    entrepreneur = db.query(Entrepreneur).filter(Entrepreneur.user_id == current_user.user_id).first()
    if not entrepreneur:
        raise HTTPException(status_code=404, detail="Profil entrepreneur non trouvé")
    
    # Vérifier que le programme existe
    program = db.query(Program).filter(Program.program_id == program_id).first()
    if not program:
        raise HTTPException(status_code=404, detail="Programme non trouvé")
    
    # Vérifier qu'il n'y a pas déjà une demande en cours
    existing_enrollment = db.query(ProgramParticipant).filter(
        ProgramParticipant.program_id == program_id,
        ProgramParticipant.entrepreneur_id == entrepreneur.entrepreneur_id
    ).first()
    
    if existing_enrollment:
        if existing_enrollment.enrollment_status == EnrollmentStatus.pending:
            raise HTTPException(status_code=400, detail="Vous avez déjà une demande en cours pour ce programme")
        elif existing_enrollment.enrollment_status == EnrollmentStatus.approved:
            raise HTTPException(status_code=400, detail="Vous êtes déjà inscrit à ce programme")
        elif existing_enrollment.enrollment_status == EnrollmentStatus.rejected:
            # Permettre une nouvelle demande si la précédente a été rejetée
            existing_enrollment.enrollment_status = EnrollmentStatus.pending
            existing_enrollment.enrollment_request_date = datetime.utcnow()
            existing_enrollment.rejection_reason = None
            db.commit()
            return {"message": "Nouvelle demande d'inscription envoyée"}
    
    # Créer une nouvelle demande d'inscription
    enrollment = ProgramParticipant(
        program_id=program_id,
        entrepreneur_id=entrepreneur.entrepreneur_id,
        enrollment_status=EnrollmentStatus.pending,
        completion_status=CompletionStatus.in_progress
    )
    
    db.add(enrollment)
    db.commit()
    
    return {
        "message": "Demande d'inscription envoyée avec succès",
        "program_name": program.name,
        "enrollment_id": str(enrollment.participant_id)
    }

@router.get("/{program_id}/enrollment-status")
def get_program_enrollment_status(
    program_id: UUID,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Vérifier le statut d'inscription à un programme"""
    
    if current_user.user_type.value != "entrepreneur":
        return {"status": "not_applicable"}
    
    entrepreneur = db.query(Entrepreneur).filter(Entrepreneur.user_id == current_user.user_id).first()
    if not entrepreneur:
        return {"status": "no_profile"}
    
    enrollment = db.query(ProgramParticipant).filter(
        ProgramParticipant.program_id == program_id,
        ProgramParticipant.entrepreneur_id == entrepreneur.entrepreneur_id
    ).first()
    
    if not enrollment:
        return {"status": "not_enrolled"}
    
    return {
        "status": enrollment.enrollment_status.value,
        "enrollment_date": enrollment.enrollment_request_date,
        "approved_date": enrollment.enrollment_approved_date,
        "rejection_reason": enrollment.rejection_reason
    }

@router.get("/{program_id}/modules/accessible")
def get_accessible_modules(
    program_id: UUID,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupérer les modules accessibles d'un programme"""
    
    # Récupérer tous les modules du programme, triés par order_index
    modules = db.query(Module).filter(
        Module.program_id == program_id,
        Module.status == ModuleStatus.published,
        Module.is_visible == True
    ).order_by(Module.order_index).all()
    
    if not modules:
        return {
            "modules": [],
            "total_modules": 0,
            "free_modules": 0,
            "full_access": False
        }
    
    # Pour les entrepreneurs, vérifier le niveau d'accès
    accessible_modules = []
    full_access = False
    
    if current_user.user_type.value == "entrepreneur":
        entrepreneur = db.query(Entrepreneur).filter(Entrepreneur.user_id == current_user.user_id).first()
        if entrepreneur:
            enrollment = db.query(ProgramParticipant).filter(
                ProgramParticipant.program_id == program_id,
                ProgramParticipant.entrepreneur_id == entrepreneur.entrepreneur_id,
                ProgramParticipant.enrollment_status == EnrollmentStatus.approved
            ).first()
            full_access = bool(enrollment)
    else:
        # Experts et admins ont accès complet
        full_access = True
    
    for i, module in enumerate(modules):
        # Les 2 premiers modules sont toujours accessibles (order_index 0 et 1)
        is_accessible = full_access or (module.order_index <= 1)
        
        module_data = {
            "module_id": str(module.module_id),
            "title": module.title,
            "description": module.description,
            "module_type": module.module_type.value,
            "difficulty_level": module.difficulty_level.value,
            "estimated_duration_minutes": module.estimated_duration_minutes,
            "order_index": module.order_index,
            "is_accessible": is_accessible,
            "is_free": module.order_index <= 1,  # Les 2 premiers sont gratuits
            "content_count": len(module.contents) if hasattr(module, 'contents') and module.contents else 0
        }
        
        # Ajouter les informations de progression si entrepreneur
        if current_user.user_type.value == "entrepreneur" and entrepreneur:
            progress = db.query(ModuleProgress).filter(
                ModuleProgress.module_id == module.module_id,
                ModuleProgress.entrepreneur_id == entrepreneur.entrepreneur_id
            ).first()
            
            if progress:
                module_data.update({
                    "completion_percentage": progress.completion_percentage,
                    "is_started": progress.is_started,
                    "is_completed": progress.is_completed,
                    "last_accessed_at": progress.last_accessed_at
                })
            else:
                module_data.update({
                    "completion_percentage": 0,
                    "is_started": False,
                    "is_completed": False,
                    "last_accessed_at": None
                })
        
        accessible_modules.append(module_data)
    
    return {
        "modules": accessible_modules,
        "total_modules": len(modules),
        "free_modules": sum(1 for m in modules if m.order_index <= 1),
        "full_access": full_access
    }

# ========== ROUTES PUBLIQUES/ENTREPRENEURS ==========

@router.get("/", response_model=List[ProgramWithParticipation])
def list_programs(
    active_only: bool = Query(True, description="Afficher seulement les programmes actifs"),
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """📋 Lister les programmes disponibles"""
    
    if active_only:
        programs = get_active_programs(db, skip, limit)
    else:
        programs = get_all_programs(db, skip, limit)
    
    # Enrichir avec infos de participation si entrepreneur
    result = []
    entrepreneur = None
    if current_user.user_type.value == "entrepreneur":
        entrepreneur = get_entrepreneur_by_user_id(db, current_user.user_id)
    
    for program in programs:
        participants_count = get_program_participants_count(db, program.program_id)
        available_spots = None
        if program.max_participants:
            available_spots = program.max_participants - participants_count
        
        program_data = ProgramWithParticipation(
            **program.__dict__,
            participants_count=participants_count,
            available_spots=available_spots
        )
        
        # Vérifier participation si entrepreneur
        if entrepreneur:
            participation = get_participation_by_ids(
                db, program.program_id, entrepreneur.entrepreneur_id
            )
            if participation:
                program_data.is_enrolled = True
                program_data.enrollment_date = participation.enrollment_request_date
                program_data.completion_status = participation.completion_status
        
        result.append(program_data)
    
    return result

@router.get("/{program_id}", response_model=ProgramWithParticipation)
def get_program_details(
    program_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """📖 Détails d'un programme"""
    program = get_program(db, program_id)
    
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Programme non trouvé"
        )
    
    participants_count = get_program_participants_count(db, program_id)
    available_spots = None
    if program.max_participants:
        available_spots = program.max_participants - participants_count
    
    program_data = ProgramWithParticipation(
        **program.__dict__,
        participants_count=participants_count,
        available_spots=available_spots
    )
    
    # Vérifier participation si entrepreneur
    if current_user.user_type.value == "entrepreneur":
        entrepreneur = get_entrepreneur_by_user_id(db, current_user.user_id)
        if entrepreneur:
            participation = get_participation_by_ids(
                db, program_id, entrepreneur.entrepreneur_id
            )
            if participation:
                program_data.is_enrolled = True
                program_data.enrollment_date = participation.enrollment_request_date
                program_data.completion_status = participation.completion_status
    
    return program_data

@router.post("/{program_id}/enroll", response_model=ProgramParticipantResponse)
def enroll_in_program(
    program_id: UUID,
    current_user: User = Depends(require_entrepreneur),
    db: Session = Depends(get_db)
):
    """📝 S'inscrire à un programme"""
    
    # Vérifier que l'entrepreneur est validé
    entrepreneur = get_entrepreneur_by_user_id(db, current_user.user_id)
    if not entrepreneur:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil entrepreneur non trouvé"
        )
    
    if entrepreneur.validation_status != ValidationStatus.approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Votre profil doit être validé pour vous inscrire à un programme"
        )
    
    # Vérifier que le programme existe
    program = get_program(db, program_id)
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Programme non trouvé"
        )
    
    if not program.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce programme n'est plus actif"
        )
    
    # Tenter inscription
    participation = enroll_entrepreneur_to_program(
        db, program_id, entrepreneur.entrepreneur_id
    )
    
    if not participation:
        # Vérifier la raison de l'échec
        existing = get_participation_by_ids(db, program_id, entrepreneur.entrepreneur_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vous êtes déjà inscrit à ce programme"
            )
        
        # Vérifier si plein
        if program.max_participants:
            current_count = get_program_participants_count(db, program_id)
            if current_count >= program.max_participants:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ce programme a atteint sa capacité maximale"
                )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de s'inscrire à ce programme"
        )
    
    return participation

@router.delete("/{program_id}/leave")
def leave_program_route(
    program_id: UUID,
    current_user: User = Depends(require_entrepreneur),
    db: Session = Depends(get_db)
):
    """🚪 Quitter un programme"""
    
    entrepreneur = get_entrepreneur_by_user_id(db, current_user.user_id)
    if not entrepreneur:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil entrepreneur non trouvé"
        )
    
    success = leave_program(db, program_id, entrepreneur.entrepreneur_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participation non trouvée"
        )
    
    return {"message": "Vous avez quitté le programme avec succès"}

@router.get("/me/summary", response_model=EntrepreneurProgramSummary)
def get_my_programs_summary(
    current_user: User = Depends(require_entrepreneur),
    db: Session = Depends(get_db)
):
    """📊 Résumé de mes programmes"""
    
    entrepreneur = get_entrepreneur_by_user_id(db, current_user.user_id)
    if not entrepreneur:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil entrepreneur non trouvé"
        )
    
    participations = get_entrepreneur_programs(db, entrepreneur.entrepreneur_id)
    
    # Calculer stats
    total = len(participations)
    active = len([p for p in participations if p.completion_status.value == "in_progress"])
    completed = len([p for p in participations if p.completion_status.value == "completed"])
    
    return EntrepreneurProgramSummary(
        total_programs=total,
        active_programs=active,
        completed_programs=completed,
        programs=participations
    )

# ========== ROUTES ADMIN ==========

@router.post("/", response_model=ProgramResponse)
def create_new_program(
    program_data: ProgramCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """➕ Créer un nouveau programme (Admin)"""
    
    program_data.created_by = current_user.user_id
    program = create_program(db, program_data)
    return program

@router.put("/{program_id}", response_model=ProgramResponse)
def update_program_route(
    program_id: UUID,
    program_data: ProgramUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """✏️ Modifier un programme (Admin)"""
    
    program = update_program(db, program_id, program_data)
    
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Programme non trouvé"
        )
    
    return program

@router.delete("/{program_id}")
def delete_program_route(
    program_id: UUID,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """🗑️ Supprimer un programme (Admin)"""
    
    program = delete_program(db, program_id)
    
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Programme non trouvé"
        )
    
    return {"message": "Programme supprimé avec succès"}

@router.get("/{program_id}/participants", response_model=List[ProgramParticipantResponse])
def get_program_participants_route(
    program_id: UUID,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """👥 Liste des participants d'un programme (Admin)"""
    
    program = get_program(db, program_id)
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Programme non trouvé"
        )
    
    participants = get_program_participants(db, program_id)
    return participants

@router.get("/{program_id}/stats", response_model=ProgramStats)
def get_program_statistics(
    program_id: UUID,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """📈 Statistiques d'un programme (Admin)"""
    
    program = get_program(db, program_id)
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Programme non trouvé"
        )
    
    participants = get_program_participants(db, program_id)
    
    total = len(participants)
    active = len([p for p in participants if p.completion_status.value == "in_progress"])
    completed = len([p for p in participants if p.completion_status.value == "completed"])
    dropped = len([p for p in participants if p.completion_status.value == "dropped"])
    
    completion_rate = (completed / total * 100) if total > 0 else 0
    
    return ProgramStats(
        total_participants=total,
        active_participants=active,
        completed_participants=completed,
        dropped_participants=dropped,
        completion_rate=round(completion_rate, 2)
    )

    # ========== GESTION DES EXPERTS ASSIGNÉS ==========

@router.get("/{program_id}/experts", response_model=List[dict])
def get_program_experts(
    program_id: UUID,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """📋 Liste des experts assignés à un programme (Admin)"""
    
    program = get_program(db, program_id)
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Programme non trouvé"
        )
    
    experts = db.query(ProgramExpert).filter(
        ProgramExpert.program_id == program_id
    ).all()
    
    # Enrichir avec les données des experts
    result = []
    for assignment in experts:
        expert = get_expert(db, assignment.expert_id)
        if expert:
            result.append({
                "program_expert_id": str(assignment.program_expert_id),
                "program_id": str(assignment.program_id),
                "expert_id": str(assignment.expert_id),
                "role": assignment.role,
                "assigned_at": assignment.assigned_at.isoformat(),
                "expert": {
                    "expert_id": str(expert.expert_id),
                    "user": {
                        "first_name": expert.user.first_name,
                        "last_name": expert.user.last_name,
                        "email": expert.user.email
                    },
                    "specialization": expert.specialization,
                    "years_of_experience": expert.years_of_experience,
                    "bio": expert.bio
                }
            })
    
    return result

@router.post("/{program_id}/experts")
def assign_expert_to_program(
    program_id: UUID,
    assignment_data: dict,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """➕ Assigner un expert à un programme (Admin)"""
    
    expert_id = assignment_data.get("expert_id")
    role = assignment_data.get("role", "mentor")
    
    if not expert_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de l'expert requis"
        )
    
    # Vérifier que le programme existe
    program = get_program(db, program_id)
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Programme non trouvé"
        )
    
    # Vérifier que l'expert existe
    expert = get_expert(db, expert_id)
    if not expert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expert non trouvé"
        )
    
    # Vérifier que l'expert n'est pas déjà assigné à ce programme
    existing = db.query(ProgramExpert).filter(
        ProgramExpert.program_id == program_id,
        ProgramExpert.expert_id == expert_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cet expert est déjà assigné à ce programme"
        )
    
    # Créer l'assignation
    assignment = ProgramExpert(
        program_id=program_id,
        expert_id=expert_id,
        role=role,
        assigned_by=current_user.user_id
    )
    
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    
    return {
        "message": "Expert assigné avec succès",
        "assignment": {
            "program_expert_id": str(assignment.program_expert_id),
            "program_id": str(assignment.program_id),
            "expert_id": str(assignment.expert_id),
            "role": assignment.role,
            "assigned_at": assignment.assigned_at.isoformat()
        }
    }

@router.delete("/{program_id}/experts/{expert_id}")
def remove_expert_from_program(
    program_id: UUID,
    expert_id: UUID,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """🗑️ Retirer un expert d'un programme (Admin)"""
    
    assignment = db.query(ProgramExpert).filter(
        ProgramExpert.program_id == program_id,
        ProgramExpert.expert_id == expert_id
    ).first()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignation non trouvée"
        )
    
    db.delete(assignment)
    db.commit()
    
    return {"message": "Expert retiré du programme avec succès"}

@router.put("/{program_id}/experts/{expert_id}")
def update_expert_role(
    program_id: UUID,
    expert_id: UUID,
    role_data: dict,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """✏️ Modifier le rôle d'un expert dans un programme (Admin)"""
    
    new_role = role_data.get("role")
    if not new_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nouveau rôle requis"
        )
    
    assignment = db.query(ProgramExpert).filter(
        ProgramExpert.program_id == program_id,
        ProgramExpert.expert_id == expert_id
    ).first()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignation non trouvée"
        )
    
    assignment.role = new_role
    db.commit()
    db.refresh(assignment)
    
    return {
        "message": "Rôle mis à jour avec succès",
        "assignment": {
            "program_expert_id": str(assignment.program_expert_id),
            "role": assignment.role
        }
    }

# ========== GESTION DES PARTICIPANTS ==========

@router.put("/{program_id}/participants/{entrepreneur_id}/status")
def update_participant_status(
    program_id: UUID,
    entrepreneur_id: UUID,
    status_data: dict,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """✏️ Modifier le statut d'un participant (Admin)"""
    
    new_status = status_data.get("completion_status")
    if not new_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nouveau statut requis"
        )
    
    # Vérifier que le statut est valide
    valid_statuses = ["in_progress", "completed", "dropped"]
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Statut invalide. Statuts valides: {', '.join(valid_statuses)}"
        )
    
    # Trouver la participation
    participation = db.query(ProgramParticipant).filter(
        ProgramParticipant.program_id == program_id,
        ProgramParticipant.entrepreneur_id == entrepreneur_id
    ).first()
    
    if not participation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participation non trouvée"
        )
    
    # Mettre à jour le statut
    participation.completion_status = new_status
    
    # Si terminé, mettre la date de completion
    if new_status == "completed":
        participation.completion_date = datetime.utcnow()
    elif new_status == "in_progress":
        # Remettre en cours annule la date de completion
        participation.completion_date = None
    
    db.commit()
    db.refresh(participation)
    
    return {
        "message": "Statut mis à jour avec succès",
        "participation": {
            "participant_id": str(participation.participant_id),
            "completion_status": participation.completion_status,
            "completion_date": participation.completion_date.isoformat() if participation.completion_date else None
        }
    }

@router.delete("/{program_id}/participants/{entrepreneur_id}")
def remove_participant_from_program(
    program_id: UUID,
    entrepreneur_id: UUID,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """🗑️ Retirer un participant d'un programme (Admin)"""
    
    participation = db.query(ProgramParticipant).filter(
        ProgramParticipant.program_id == program_id,
        ProgramParticipant.entrepreneur_id == entrepreneur_id
    ).first()
    
    if not participation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participation non trouvée"
        )
    
    db.delete(participation)
    db.commit()
    
    return {"message": "Participant retiré du programme avec succès"}

@router.get("/admin/enrollments")
def get_all_enrollments(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """📋 Récupérer toutes les inscriptions (Admin)"""
    
    enrollments = db.query(ProgramParticipant).join(
        Program, ProgramParticipant.program_id == Program.program_id
    ).join(
        Entrepreneur, ProgramParticipant.entrepreneur_id == Entrepreneur.entrepreneur_id
    ).join(
        User, Entrepreneur.user_id == User.user_id
    ).all()
    
    result = []
    for participation in enrollments:
        result.append({
            "participant_id": str(participation.participant_id),
            "program_id": str(participation.program_id),
            "program_name": participation.program.name,
            "enrollment_date": participation.enrollment_request_date.isoformat(),
            "completion_status": participation.completion_status,
            "completion_date": participation.completion_date.isoformat() if participation.completion_date else None,
            "entrepreneur": {
                "entrepreneur_id": str(participation.entrepreneur.entrepreneur_id),
                "company_name": participation.entrepreneur.company_name,
                "industry_sector": participation.entrepreneur.industry_sector,
                "user": {
                    "first_name": participation.entrepreneur.user.first_name,
                    "last_name": participation.entrepreneur.user.last_name,
                    "email": participation.entrepreneur.user.email
                }
            }
        })
    
    return result

    # À ajouter dans app/routes/program.py

# Routes pour l'admin (gestion des inscriptions)
@router.get("/admin/programs/{program_id}/enrollments", dependencies=[Depends(require_admin)])
def get_program_enrollments(
    program_id: UUID,
    status: Optional[str] = Query(None, description="Filtrer par statut: pending, approved, rejected"),
    db: Session = Depends(get_db)
):
    """Récupérer les demandes d'inscription à un programme"""
    
    query = db.query(ProgramParticipant).filter(ProgramParticipant.program_id == program_id)
    
    if status:
        query = query.filter(ProgramParticipant.enrollment_status == status)
    
    enrollments = query.order_by(desc(ProgramParticipant.enrollment_request_date)).all()
    
    result = []
    for enrollment in enrollments:
        entrepreneur = enrollment.entrepreneur
        user = entrepreneur.user
        
        result.append({
            "participant_id": str(enrollment.participant_id),
            "entrepreneur_id": str(entrepreneur.entrepreneur_id),
            "user_id": str(user.user_id),
            "entrepreneur_name": f"{user.first_name} {user.last_name}",
            "company_name": entrepreneur.company_name,
            "email": user.email,
            "enrollment_status": enrollment.enrollment_status.value,
            "completion_status": enrollment.completion_status.value,
            "enrollment_request_date": enrollment.enrollment_request_date,
            "enrollment_approved_date": enrollment.enrollment_approved_date,
            "rejection_reason": enrollment.rejection_reason,
            "company_description": entrepreneur.company_description,
            "industry_sector": entrepreneur.industry_sector
        })
    
    return result

@router.put("/admin/programs/{program_id}/enrollments/{participant_id}/approve", dependencies=[Depends(require_admin)])
def approve_program_enrollment(
    program_id: UUID,
    participant_id: UUID,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Approuver une demande d'inscription"""
    
    enrollment = db.query(ProgramParticipant).filter(
        ProgramParticipant.participant_id == participant_id,
        ProgramParticipant.program_id == program_id
    ).first()
    
    if not enrollment:
        raise HTTPException(status_code=404, detail="Demande d'inscription non trouvée")
    
    if enrollment.enrollment_status != EnrollmentStatus.pending:
        raise HTTPException(status_code=400, detail="Cette demande n'est pas en attente")
    
    # Approuver l'inscription
    enrollment.enrollment_status = EnrollmentStatus.approved
    enrollment.enrollment_approved_date = datetime.utcnow()
    enrollment.approved_by = current_user.user_id
    enrollment.rejection_reason = None
    
    db.commit()
    
    # TODO: Envoyer notification à l'entrepreneur
    
    return {
        "message": "Inscription approuvée avec succès",
        "participant_id": str(enrollment.participant_id)
    }

@router.put("/admin/programs/{program_id}/enrollments/{participant_id}/reject", dependencies=[Depends(require_admin)])
def reject_program_enrollment(
    program_id: UUID,
    participant_id: UUID,
    rejection_data: dict,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Rejeter une demande d'inscription"""
    
    enrollment = db.query(ProgramParticipant).filter(
        ProgramParticipant.participant_id == participant_id,
        ProgramParticipant.program_id == program_id
    ).first()
    
    if not enrollment:
        raise HTTPException(status_code=404, detail="Demande d'inscription non trouvée")
    
    if enrollment.enrollment_status != EnrollmentStatus.pending:
        raise HTTPException(status_code=400, detail="Cette demande n'est pas en attente")
    
    # Rejeter l'inscription
    enrollment.enrollment_status = EnrollmentStatus.rejected
    enrollment.approved_by = current_user.user_id
    enrollment.rejection_reason = rejection_data.get("reason", "Aucune raison spécifiée")
    
    db.commit()
    
    # TODO: Envoyer notification à l'entrepreneur
    
    return {
        "message": "Inscription rejetée",
        "participant_id": str(enrollment.participant_id),
        "reason": enrollment.rejection_reason
    }