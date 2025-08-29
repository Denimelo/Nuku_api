from sqlalchemy.orm import Session
from sqlalchemy import and_
from uuid import UUID
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.models.programExpert import ProgramExpert
from app.models.program import Program
from app.models.expert import Expert
from app.models.user import User

def assign_expert_to_program(
    db: Session,
    program_id: UUID,
    expert_id: UUID,
    role: str,
    assigned_by: UUID
) -> Optional[ProgramExpert]:
    """Assigner un expert à un programme"""
    
    # Vérifier si déjà assigné
    existing = db.query(ProgramExpert).filter(
        and_(
            ProgramExpert.program_id == program_id,
            ProgramExpert.expert_id == expert_id
        )
    ).first()
    
    if existing:
        return None  # Déjà assigné
    
    # Créer assignment
    assignment = ProgramExpert(
        program_id=program_id,
        expert_id=expert_id,
        role=role,
        assigned_by=assigned_by
    )
    
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment

def get_expert_programs(db: Session, expert_id: UUID) -> List[ProgramExpert]:
    """Programmes assignés à un expert"""
    return db.query(ProgramExpert).filter(
        ProgramExpert.expert_id == expert_id
    ).all()

def get_program_experts(db: Session, program_id: UUID) -> List[ProgramExpert]:
    """Experts assignés à un programme"""
    return db.query(ProgramExpert).filter(
        ProgramExpert.program_id == program_id
    ).all()

def remove_expert_from_program(
    db: Session,
    program_id: UUID,
    expert_id: UUID
) -> bool:
    """Retirer un expert d'un programme"""
    assignment = db.query(ProgramExpert).filter(
        and_(
            ProgramExpert.program_id == program_id,
            ProgramExpert.expert_id == expert_id
        )
    ).first()
    
    if not assignment:
        return False
    
    db.delete(assignment)
    db.commit()
    return True

def update_expert_role_in_program(
    db: Session,
    program_id: UUID,
    expert_id: UUID,
    new_role: str
) -> Optional[ProgramExpert]:
    """Modifier le rôle d'un expert dans un programme"""
    assignment = db.query(ProgramExpert).filter(
        and_(
            ProgramExpert.program_id == program_id,
            ProgramExpert.expert_id == expert_id
        )
    ).first()
    
    if not assignment:
        return None
    
    assignment.role = new_role
    db.commit()
    db.refresh(assignment)
    return assignment

def get_expert_assignment(
    db: Session,
    program_id: UUID,
    expert_id: UUID
) -> Optional[ProgramExpert]:
    """Récupérer assignment spécifique"""
    return db.query(ProgramExpert).filter(
        and_(
            ProgramExpert.program_id == program_id,
            ProgramExpert.expert_id == expert_id
        )
    ).first()

def get_expert_programs_with_details(db: Session, expert_id: UUID) -> List[Dict[str, Any]]:
    """Programmes d'un expert avec détails complets"""
    assignments = db.query(ProgramExpert).filter(
        ProgramExpert.expert_id == expert_id
    ).all()
    
    programs_details = []
    
    for assignment in assignments:
        program = assignment.program
        if program:
            # Compter participants
            from app.crud.program import get_program_participants_count
            participants_count = get_program_participants_count(db, program.program_id)
            
            programs_details.append({
                "program_expert_id": str(assignment.program_expert_id),
                "program_id": str(program.program_id),
                "program_name": program.name,
                "participants_count": participants_count,
                "start_date": program.start_date,
                "end_date": program.end_date,
                "is_active": program.is_active,
                "role": assignment.role,
                "assigned_at": assignment.assigned_at
            })
    
    return programs_details

def get_expert_entrepreneurs_in_programs(db: Session, expert_id: UUID) -> List[Dict[str, Any]]:
    """Entrepreneurs dans les programmes de l'expert"""
    from app.models.programParticipant import ProgramParticipant
    from app.models.entrepreneur import Entrepreneur
    
    # Récupérer les programmes de l'expert
    expert_programs = db.query(ProgramExpert.program_id).filter(
        ProgramExpert.expert_id == expert_id
    ).subquery()
    
    # Récupérer les participants de ces programmes
    participants = db.query(ProgramParticipant).filter(
        ProgramParticipant.program_id.in_(expert_programs)
    ).all()
    
    entrepreneurs_details = []
    
    for participant in participants:
        entrepreneur = participant.entrepreneur
        if entrepreneur and entrepreneur.user:
            entrepreneurs_details.append({
                "entrepreneur_id": str(entrepreneur.entrepreneur_id),
                "entrepreneur_name": f"{entrepreneur.user.first_name} {entrepreneur.user.last_name}",
                "company_name": entrepreneur.company_name,
                "industry_sector": entrepreneur.industry_sector,
                "enrollment_request_date": participant.enrollment_request_date,
                "completion_status": participant.completion_status.value,
                "program_id": str(participant.program_id),
                "program_name": participant.program.name if participant.program else "N/A"
            })
    
    return entrepreneurs_details