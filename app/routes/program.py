from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.database import get_db
from app.auth.dependencies import get_current_user, require_admin, require_entrepreneur
from app.models.user import User
from app.models.entrepreneur import ValidationStatus
from app.schemas.program import (
    ProgramResponse, ProgramCreate, ProgramUpdate, ProgramWithParticipation,
    ProgramParticipantResponse, ProgramStats, EntrepreneurProgramSummary,
    CompletionStatusSchema
)
from app.crud.program import (
    get_all_programs, get_active_programs, create_program, get_program,
    update_program, delete_program, enroll_entrepreneur_to_program,
    get_entrepreneur_programs, get_program_participants, get_program_participants_count,
    leave_program, get_participation_by_ids, update_participation_status
)
from app.crud.entrepreneur import get_entrepreneur_by_user_id

router = APIRouter(prefix="/programs", tags=["Programs"])

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
                program_data.enrollment_date = participation.enrollment_date
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
                program_data.enrollment_date = participation.enrollment_date
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