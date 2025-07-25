from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, asc, func
from uuid import UUID
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from app.models.assignment import Assignment, AssignmentType, AssignmentStatus
from app.models.assignmentSubmission import AssignmentSubmission, SubmissionStatus
from app.models.entrepreneur import Entrepreneur
from app.models.expert import Expert
from app.models.module import Module
from app.schemas.assignment import AssignmentCreate, AssignmentUpdate, AssignmentSubmissionCreate, AssignmentSubmissionUpdate, GradeSubmissionRequest

# ========== CRUD ASSIGNMENT ==========

def create_assignment(db: Session, assignment_data: AssignmentCreate, created_by: UUID) -> Assignment:
    """Créer un nouveau devoir"""
    
    assignment = Assignment(
        **assignment_data.dict(),
        created_by=created_by
    )
    
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment

def get_assignment_by_id(db: Session, assignment_id: UUID) -> Optional[Assignment]:
    """Récupérer assignment par ID avec relations"""
    return db.query(Assignment).options(
        joinedload(Assignment.module),
        joinedload(Assignment.created_by_expert).joinedload(Expert.user),
        joinedload(Assignment.submissions)
    ).filter(Assignment.assignment_id == assignment_id).first()

def get_assignments_by_module(
    db: Session, 
    module_id: UUID,
    published_only: bool = True
) -> List[Assignment]:
    """Récupérer assignments d'un module"""
    query = db.query(Assignment).options(
        joinedload(Assignment.created_by_expert).joinedload(Expert.user)
    ).filter(Assignment.module_id == module_id)
    
    if published_only:
        query = query.filter(Assignment.status == AssignmentStatus.published)
    
    return query.order_by(Assignment.created_at).all()

def get_assignments_by_expert(db: Session, expert_id: UUID) -> List[Assignment]:
    """Assignments créés par un expert"""
    return db.query(Assignment).options(
        joinedload(Assignment.module),
        joinedload(Assignment.submissions)
    ).filter(Assignment.created_by == expert_id).order_by(desc(Assignment.created_at)).all()

def get_assignments_for_entrepreneur(
    db: Session,
    entrepreneur_id: UUID,
    program_id: Optional[UUID] = None,
    include_completed: bool = True
) -> List[Dict[str, Any]]:
    """Assignments disponibles pour un entrepreneur"""
    
    # Construire requête pour récupérer assignments via modules du programme
    query = db.query(Assignment).options(
        joinedload(Assignment.module),
        joinedload(Assignment.created_by_expert).joinedload(Expert.user)
    ).join(Module)
    
    if program_id:
        query = query.filter(Module.program_id == program_id)
    
    query = query.filter(
        Assignment.status == AssignmentStatus.published,
        Module.status == "published",
        Module.is_visible == True
    )
    
    assignments = query.all()
    
    # Enrichir avec soumissions de l'entrepreneur
    result = []
    for assignment in assignments:
        # Récupérer soumission de l'entrepreneur
        submission = db.query(AssignmentSubmission).filter(
            AssignmentSubmission.assignment_id == assignment.assignment_id,
            AssignmentSubmission.entrepreneur_id == entrepreneur_id
        ).order_by(desc(AssignmentSubmission.created_at)).first()
        
        # Filtrer selon les critères
        if not include_completed and submission and submission.status == SubmissionStatus.submitted:
            continue
        
        assignment_data = {
            "assignment": assignment,
            "user_submission": submission,
            "user_attempts_used": _count_user_attempts(db, assignment.assignment_id, entrepreneur_id),
            "user_can_submit": _can_user_submit(assignment, submission),
            "is_available": assignment.is_available,
            "is_overdue": assignment.is_overdue
        }
        
        result.append(assignment_data)
    
    return result

def update_assignment(
    db: Session, 
    assignment_id: UUID, 
    update_data: AssignmentUpdate,
    user_id: UUID
) -> Optional[Assignment]:
    """Mettre à jour assignment"""
    assignment = db.query(Assignment).filter(Assignment.assignment_id == assignment_id).first()
    
    if not assignment:
        return None
    
    # TODO: Vérifier permissions (créateur ou admin)
    
    for field, value in update_data.dict(exclude_unset=True).items():
        if hasattr(assignment, field):
            setattr(assignment, field, value)
    
    assignment.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(assignment)
    return assignment

def delete_assignment(db: Session, assignment_id: UUID, user_id: UUID) -> bool:
    """Supprimer assignment"""
    assignment = db.query(Assignment).filter(Assignment.assignment_id == assignment_id).first()
    
    if not assignment:
        return False
    
    # TODO: Vérifier permissions
    
    db.delete(assignment)
    db.commit()
    return True

def publish_assignment(db: Session, assignment_id: UUID, user_id: UUID) -> Optional[Assignment]:
    """Publier un assignment"""
    assignment = db.query(Assignment).filter(Assignment.assignment_id == assignment_id).first()
    
    if not assignment:
        return None
    
    assignment.status = AssignmentStatus.published
    assignment.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(assignment)
    return assignment

# ========== CRUD ASSIGNMENT SUBMISSION ==========

def create_or_update_submission(
    db: Session,
    submission_data: AssignmentSubmissionCreate,
    entrepreneur_id: UUID,
    ip_address: Optional[str] = None
) -> Optional[AssignmentSubmission]:
    """Créer ou mettre à jour une soumission"""
    
    assignment = get_assignment_by_id(db, submission_data.assignment_id)
    if not assignment or not assignment.is_available:
        return None
    
    # Vérifier limites de tentatives
    attempts_used = _count_user_attempts(db, submission_data.assignment_id, entrepreneur_id)
    if attempts_used >= assignment.max_attempts:
        return None
    
    # Chercher brouillon existant
    existing_draft = db.query(AssignmentSubmission).filter(
        AssignmentSubmission.assignment_id == submission_data.assignment_id,
        AssignmentSubmission.entrepreneur_id == entrepreneur_id,
        AssignmentSubmission.status == SubmissionStatus.draft
    ).first()
    
    if existing_draft:
        # Mettre à jour brouillon existant
        existing_draft.submission_text = submission_data.submission_text
        existing_draft.submission_files = submission_data.submission_files
        existing_draft.updated_at = datetime.utcnow()
        submission = existing_draft
    else:
        # Créer nouvelle soumission
        submission = AssignmentSubmission(
            assignment_id=submission_data.assignment_id,
            entrepreneur_id=entrepreneur_id,
            submission_text=submission_data.submission_text,
            submission_files=submission_data.submission_files,
            attempt_number=attempts_used + 1,
            ip_address=ip_address
        )
        db.add(submission)
    
    db.commit()
    db.refresh(submission)
    return submission

def submit_assignment(
    db: Session,
    submission_id: UUID,
    entrepreneur_id: UUID,
    time_spent: Optional[int] = None
) -> Optional[AssignmentSubmission]:
    """Soumettre définitivement un assignment"""
    
    submission = db.query(AssignmentSubmission).filter(
        AssignmentSubmission.submission_id == submission_id,
        AssignmentSubmission.entrepreneur_id == entrepreneur_id,
        AssignmentSubmission.status == SubmissionStatus.draft
    ).first()
    
    if not submission:
        return None
    
    # Vérifier que l'assignment est encore disponible
    if not submission.assignment.is_available:
        return None
    
    submission.status = SubmissionStatus.submitted
    submission.submitted_at = datetime.utcnow()
    
    if time_spent:
        submission.time_spent_minutes = time_spent
    
    # Mettre à jour compteur de l'assignment
    assignment = submission.assignment
    assignment.submission_count += 1
    
    db.commit()
    db.refresh(submission)
    return submission

def get_submission_by_id(
    db: Session, 
    submission_id: UUID,
    user_id: Optional[UUID] = None
) -> Optional[AssignmentSubmission]:
    """Récupérer soumission par ID"""
    query = db.query(AssignmentSubmission).options(
        joinedload(AssignmentSubmission.assignment),
        joinedload(AssignmentSubmission.entrepreneur).joinedload(Entrepreneur.user),
        joinedload(AssignmentSubmission.graded_by_expert).joinedload(Expert.user)
    ).filter(AssignmentSubmission.submission_id == submission_id)
    
    # Si user_id fourni, vérifier permissions
    if user_id:
        query = query.filter(
            or_(
                AssignmentSubmission.entrepreneur_id == user_id,
                AssignmentSubmission.graded_by == user_id
            )
        )
    
    return query.first()

def get_submissions_for_grading(
    db: Session,
    expert_id: Optional[UUID] = None,
    assignment_id: Optional[UUID] = None,
    status: Optional[SubmissionStatus] = None
) -> List[AssignmentSubmission]:
    """Récupérer soumissions à évaluer"""
    
    query = db.query(AssignmentSubmission).options(
        joinedload(AssignmentSubmission.assignment),
        joinedload(AssignmentSubmission.entrepreneur).joinedload(Entrepreneur.user)
    )
    
    if expert_id:
        # Filtrer par assignments créés par cet expert
        query = query.join(Assignment).filter(Assignment.created_by == expert_id)
    
    if assignment_id:
        query = query.filter(AssignmentSubmission.assignment_id == assignment_id)
    
    if status:
        query = query.filter(AssignmentSubmission.status == status)
    else:
        # Par défaut, soumissions en attente d'évaluation
        query = query.filter(AssignmentSubmission.status == SubmissionStatus.submitted)
    
    return query.order_by(AssignmentSubmission.submitted_at).all()

def grade_submission(
    db: Session,
    submission_id: UUID,
    grade_data: GradeSubmissionRequest,
    graded_by: UUID
) -> Optional[AssignmentSubmission]:
    """Évaluer une soumission"""
    
    submission = db.query(AssignmentSubmission).filter(
        AssignmentSubmission.submission_id == submission_id
    ).first()
    
    if not submission or submission.status != SubmissionStatus.submitted:
        return None
    
    # Vérifier que le score est valide
    if grade_data.score > submission.assignment.max_score:
        return None
    
    submission.score = grade_data.score
    submission.grade = grade_data.grade
    submission.feedback = grade_data.feedback
    submission.graded_by = graded_by
    submission.graded_at = datetime.utcnow()
    submission.status = SubmissionStatus.graded
    
    # Mettre à jour moyenne de l'assignment
    _update_assignment_average(db, submission.assignment_id)
    
    db.commit()
    db.refresh(submission)
    return submission

def get_user_submissions(
    db: Session,
    entrepreneur_id: UUID,
    assignment_id: Optional[UUID] = None
) -> List[AssignmentSubmission]:
    """Récupérer soumissions d'un entrepreneur"""
    
    query = db.query(AssignmentSubmission).options(
        joinedload(AssignmentSubmission.assignment).joinedload(Assignment.module),
        joinedload(AssignmentSubmission.graded_by_expert).joinedload(Expert.user)
    ).filter(AssignmentSubmission.entrepreneur_id == entrepreneur_id)
    
    if assignment_id:
        query = query.filter(AssignmentSubmission.assignment_id == assignment_id)
    
    return query.order_by(desc(AssignmentSubmission.created_at)).all()

# ========== STATISTIQUES ==========

def get_assignment_stats(db: Session, assignment_id: UUID) -> Dict[str, Any]:
    """Statistiques d'un assignment"""
    
    submissions = db.query(AssignmentSubmission).filter(
        AssignmentSubmission.assignment_id == assignment_id
    ).all()
    
    total_submissions = len(submissions)
    graded_submissions = len([s for s in submissions if s.status == SubmissionStatus.graded])
    pending_submissions = len([s for s in submissions if s.status == SubmissionStatus.submitted])
    
    # Scores
    graded_scores = [s.score for s in submissions if s.score is not None]
    average_score = sum(graded_scores) / len(graded_scores) if graded_scores else 0
    
    # Taux de réussite
    assignment = db.query(Assignment).filter(Assignment.assignment_id == assignment_id).first()
    passing_scores = [s for s in graded_scores if s >= assignment.passing_score] if assignment else []
    passing_rate = len(passing_scores) / len(graded_scores) * 100 if graded_scores else 0
    
    # Soumissions à temps
    on_time = len([s for s in submissions if s.submitted_at and assignment and assignment.due_date and s.submitted_at <= assignment.due_date])
    late_submissions = total_submissions - on_time
    
    return {
        "total_submissions": total_submissions,
        "graded_submissions": graded_submissions,
        "pending_submissions": pending_submissions,
        "average_score": round(average_score, 2),
        "passing_rate": round(passing_rate, 2),
        "on_time_submissions": on_time,
        "late_submissions": late_submissions,
        "completion_rate": round((total_submissions / 100) * 100, 2) if total_submissions > 0 else 0  # TODO: Calculer vraiment
    }

def get_entrepreneur_assignment_summary(
    db: Session,
    entrepreneur_id: UUID,
    program_id: Optional[UUID] = None
) -> Dict[str, Any]:
    """Résumé des assignments pour un entrepreneur"""
    
    # Récupérer toutes les soumissions
    query = db.query(AssignmentSubmission).options(
        joinedload(AssignmentSubmission.assignment).joinedload(Assignment.module)
    ).filter(AssignmentSubmission.entrepreneur_id == entrepreneur_id)
    
    if program_id:
        query = query.join(Assignment).join(Module).filter(Module.program_id == program_id)
    
    submissions = query.all()
    
    # Calculer stats
    total_assignments = len(set(s.assignment_id for s in submissions))
    completed_assignments = len([s for s in submissions if s.status == SubmissionStatus.graded])
    pending_assignments = len([s for s in submissions if s.status == SubmissionStatus.submitted])
    
    # Assignments en retard
    overdue_assignments = 0
    for submission in submissions:
        if submission.assignment.due_date and datetime.utcnow() > submission.assignment.due_date and submission.status == SubmissionStatus.draft:
            overdue_assignments += 1
    
    # Score moyen
    graded_scores = [s.score for s in submissions if s.score is not None]
    average_score = sum(graded_scores) / len(graded_scores) if graded_scores else 0
    
    return {
        "total_assignments": total_assignments,
        "completed_assignments": completed_assignments,
        "pending_assignments": pending_assignments,
        "overdue_assignments": overdue_assignments,
        "average_score": round(average_score, 2),
        "submissions": submissions
    }

# ========== FONCTIONS UTILITAIRES ==========

def _count_user_attempts(db: Session, assignment_id: UUID, entrepreneur_id: UUID) -> int:
    """Compter tentatives d'un utilisateur"""
    return db.query(AssignmentSubmission).filter(
        AssignmentSubmission.assignment_id == assignment_id,
        AssignmentSubmission.entrepreneur_id == entrepreneur_id
    ).count()

def _can_user_submit(assignment: Assignment, submission: Optional[AssignmentSubmission]) -> bool:
    """Vérifier si l'utilisateur peut soumettre"""
    
    if not assignment.is_available:
        return False
    
    if submission and submission.status == SubmissionStatus.submitted:
        return False  # Déjà soumis
    
    # TODO: Vérifier autres conditions (tentatives, etc.)
    
    return True

def _update_assignment_average(db: Session, assignment_id: UUID):
    """Mettre à jour score moyen d'un assignment"""
    
    average = db.query(func.avg(AssignmentSubmission.score)).filter(
        AssignmentSubmission.assignment_id == assignment_id,
        AssignmentSubmission.score.isnot(None)
    ).scalar()
    
    if average:
        assignment = db.query(Assignment).filter(Assignment.assignment_id == assignment_id).first()
        if assignment:
            assignment.average_score = float(average)
            db.commit()

def search_assignments(
    db: Session,
    query: str,
    assignment_type: Optional[AssignmentType] = None,
    module_id: Optional[UUID] = None,
    expert_id: Optional[UUID] = None,
    limit: int = 20
) -> List[Assignment]:
    """Rechercher assignments"""
    
    search_query = db.query(Assignment).options(
        joinedload(Assignment.module),
        joinedload(Assignment.created_by_expert).joinedload(Expert.user)
    ).filter(Assignment.status == AssignmentStatus.published)
    
    if query:
        search_query = search_query.filter(
            or_(
                Assignment.title.ilike(f"%{query}%"),
                Assignment.description.ilike(f"%{query}%")
            )
        )
    
    if assignment_type:
        search_query = search_query.filter(Assignment.assignment_type == assignment_type)
    
    if module_id:
        search_query = search_query.filter(Assignment.module_id == module_id)
    
    if expert_id:
        search_query = search_query.filter(Assignment.created_by == expert_id)
    
    return search_query.order_by(desc(Assignment.created_at)).limit(limit).all()