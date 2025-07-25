from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from uuid import UUID
from typing import List, Optional
from datetime import datetime, date
from app.models.program import Program
from app.models.programParticipant import ProgramParticipant, CompletionStatus
from app.models.entrepreneur import Entrepreneur
from app.schemas.program import ProgramCreate, ProgramUpdate

# ========== CRUD PROGRAM ==========

def create_program(db: Session, program_in: ProgramCreate) -> Program:
    program = Program(**program_in.dict())
    db.add(program)
    db.commit()
    db.refresh(program)
    return program

def get_program(db: Session, program_id: UUID) -> Optional[Program]:
    return db.query(Program).filter(Program.program_id == program_id).first()

def get_all_programs(db: Session, skip: int = 0, limit: int = 100) -> List[Program]:
    return db.query(Program).offset(skip).limit(limit).all()

def get_active_programs(db: Session, skip: int = 0, limit: int = 100) -> List[Program]:
    """Récupérer seulement les programmes actifs"""
    return db.query(Program).filter(
        Program.is_active == True,
        Program.end_date >= date.today()
    ).offset(skip).limit(limit).all()

def get_programs_by_creator(db: Session, creator_id: UUID) -> List[Program]:
    """Programmes créés par un utilisateur spécifique"""
    return db.query(Program).filter(Program.created_by == creator_id).all()

def update_program(db: Session, program_id: UUID, program_in: ProgramUpdate) -> Optional[Program]:
    program = db.query(Program).filter(Program.program_id == program_id).first()
    if not program:
        return None
    
    for field, value in program_in.dict(exclude_unset=True).items():
        setattr(program, field, value)
    
    program.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(program)
    return program

def delete_program(db: Session, program_id: UUID) -> Optional[Program]:
    program = db.query(Program).filter(Program.program_id == program_id).first()
    if not program:
        return None
    db.delete(program)
    db.commit()
    return program

# ========== CRUD PROGRAM PARTICIPANT ==========

def enroll_entrepreneur_to_program(
    db: Session, 
    program_id: UUID, 
    entrepreneur_id: UUID
) -> Optional[ProgramParticipant]:
    """Inscrire un entrepreneur à un programme"""
    
    # Vérifier si déjà inscrit
    existing = db.query(ProgramParticipant).filter(
        and_(
            ProgramParticipant.program_id == program_id,
            ProgramParticipant.entrepreneur_id == entrepreneur_id
        )
    ).first()
    
    if existing:
        return None  # Déjà inscrit
    
    # Vérifier si le programme a de la place
    program = get_program(db, program_id)
    if not program or not program.is_active:
        return None
    
    if program.max_participants:
        current_participants = get_program_participants_count(db, program_id)
        if current_participants >= program.max_participants:
            return None  # Programme plein
    
    # Créer participation
    participation = ProgramParticipant(
        program_id=program_id,
        entrepreneur_id=entrepreneur_id,
        completion_status=CompletionStatus.in_progress
    )
    
    db.add(participation)
    db.commit()
    db.refresh(participation)
    return participation

def get_entrepreneur_programs(db: Session, entrepreneur_id: UUID) -> List[ProgramParticipant]:
    """Programmes d'un entrepreneur"""
    return db.query(ProgramParticipant).filter(
        ProgramParticipant.entrepreneur_id == entrepreneur_id
    ).all()

def get_program_participants(db: Session, program_id: UUID) -> List[ProgramParticipant]:
    """Participants d'un programme"""
    return db.query(ProgramParticipant).filter(
        ProgramParticipant.program_id == program_id
    ).all()

def get_program_participants_count(db: Session, program_id: UUID) -> int:
    """Nombre de participants d'un programme"""
    return db.query(ProgramParticipant).filter(
        ProgramParticipant.program_id == program_id
    ).count()

def update_participation_status(
    db: Session,
    participation_id: UUID,
    status: CompletionStatus,
    completion_date: Optional[datetime] = None
) -> Optional[ProgramParticipant]:
    """Mettre à jour le statut de participation"""
    participation = db.query(ProgramParticipant).filter(
        ProgramParticipant.participant_id == participation_id
    ).first()
    
    if not participation:
        return None
    
    participation.completion_status = status
    if status == CompletionStatus.completed and completion_date:
        participation.completion_date = completion_date
    
    db.commit()
    db.refresh(participation)
    return participation

def leave_program(
    db: Session,
    program_id: UUID,
    entrepreneur_id: UUID
) -> bool:
    """Quitter un programme"""
    participation = db.query(ProgramParticipant).filter(
        and_(
            ProgramParticipant.program_id == program_id,
            ProgramParticipant.entrepreneur_id == entrepreneur_id
        )
    ).first()
    
    if not participation:
        return False
    
    participation.completion_status = CompletionStatus.dropped
    participation.completion_date = datetime.utcnow()
    
    db.commit()
    return True

def get_participation_by_ids(
    db: Session,
    program_id: UUID,
    entrepreneur_id: UUID
) -> Optional[ProgramParticipant]:
    """Récupérer une participation spécifique"""
    return db.query(ProgramParticipant).filter(
        and_(
            ProgramParticipant.program_id == program_id,
            ProgramParticipant.entrepreneur_id == entrepreneur_id
        )
    ).first()