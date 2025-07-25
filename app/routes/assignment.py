from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.auth.dependencies import get_current_user, require_expert, require_entrepreneur
from app.models.user import User
from app.schemas.assignment import (
    AssignmentCreate, AssignmentUpdate, AssignmentResponse, AssignmentSubmissionCreate,
    AssignmentSubmissionUpdate, AssignmentSubmissionResponse, GradeSubmissionRequest,
    GradeSubmissionResponse, AssignmentStats, SubmissionSummary, AssignmentListItem,
    AssignmentFilter
)
from app.crud.assignment import (
    create_assignment, get_assignment_by_id, get_assignments_by_module,
    get_assignments_by_expert, get_assignments_for_entrepreneur, update_assignment,
    delete_assignment, publish_assignment, create_or_update_submission, submit_assignment,
    get_submission_by_id, get_submissions_for_grading, grade_submission, get_user_submissions,
    get_assignment_stats, get_entrepreneur_assignment_summary, search_assignments
)
from app.crud.expert import get_expert_by_user_id
from app.crud.entrepreneur import get_entrepreneur_by_user_id
from app.crud.module import get_module_by_id
from app.utils.supabase_storage import storage, get_content_type

router = APIRouter(prefix="/assignments", tags=["Assignments"])

def format_assignment_response(assignment, current_user_id: UUID, user_submission=None) -> dict:
    """Formater réponse assignment"""
    
    return {
        "assignment_id": assignment.assignment_id,
        "module_id": assignment.module_id,
        "title": assignment.title,
        "description": assignment.description,
        "instructions": assignment.instructions,
        "assignment_type": assignment.assignment_type,
        "max_score": assignment.max_score,
        "passing_score": assignment.passing_score,
        "due_date": assignment.due_date,
        "available_from": assignment.available_from,
        "available_until": assignment.available_until,
        "max_attempts": assignment.max_attempts,
        "time_limit_minutes": assignment.time_limit_minutes,
        "status": assignment.status,
        "is_graded": assignment.is_graded,
        "allow_late_submission": assignment.allow_late_submission,
        "created_by": assignment.created_by,
        "created_at": assignment.created_at,
        "updated_at": assignment.updated_at,
        "submission_count": assignment.submission_count,
        "average_score": assignment.average_score,
        "creator_name": f"{assignment.created_by_expert.user.first_name} {assignment.created_by_expert.user.last_name}" if assignment.created_by_expert and assignment.created_by_expert.user else None,
        "module_title": assignment.module.title if assignment.module else None,
        "is_available": assignment.is_available,
        "is_overdue": assignment.is_overdue,
        "time_remaining_hours": assignment.time_remaining.total_seconds() / 3600 if assignment.time_remaining else None,
        "user_submission": format_submission_response(user_submission, current_user_id) if user_submission else None,
        "user_attempts_used": 0,  # À calculer
        "user_can_submit": True   # À calculer
    }

def format_submission_response(submission, current_user_id: UUID) -> dict:
    """Formater réponse soumission"""
    if not submission:
        return None
    
    return {
        "submission_id": submission.submission_id,
        "assignment_id": submission.assignment_id,
        "entrepreneur_id": submission.entrepreneur_id,
        "submission_text": submission.submission_text,
        "submission_files": submission.submission_files,
        "status": submission.status,
        "attempt_number": submission.attempt_number,
        "score": submission.score,
        "grade": submission.grade,
        "feedback": submission.feedback,
        "graded_by": submission.graded_by,
        "submitted_at": submission.submitted_at,
        "graded_at": submission.graded_at,
        "created_at": submission.created_at,
        "updated_at": submission.updated_at,
        "time_spent_minutes": submission.time_spent_minutes,
        "assignment_title": submission.assignment.title if submission.assignment else None,
        "grader_name": f"{submission.graded_by_expert.user.first_name} {submission.graded_by_expert.user.last_name}" if submission.graded_by_expert and submission.graded_by_expert.user else None,
        "is_late": submission.is_late,
        "is_passing": submission.is_passing,
        "grade_percentage": submission.grade_percentage
    }

# ========== ROUTES ASSIGNMENT (CRÉATION/GESTION) ==========

@router.post("/", response_model=AssignmentResponse)
def create_new_assignment(
    assignment_data: AssignmentCreate,
    current_user: User = Depends(require_expert),
    db: Session = Depends(get_db)
):
    """📝 Créer un nouveau devoir (Expert)"""
    
    # Vérifier que le module existe
    module = get_module_by_id(db, assignment_data.module_id)
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module non trouvé"
        )
    
    # Récupérer expert ID
    expert = get_expert_by_user_id(db, current_user.user_id)
    if not expert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil expert non trouvé"
        )
    
    assignment = create_assignment(db, assignment_data, expert.expert_id)
    
    return AssignmentResponse(**format_assignment_response(assignment, current_user.user_id))

@router.get("/{assignment_id}", response_model=AssignmentResponse)
def get_assignment_details(
    assignment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """📖 Détails d'un devoir"""
    
    assignment = get_assignment_by_id(db, assignment_id)
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Devoir non trouvé"
        )
    
    # Récupérer soumission de l'utilisateur si entrepreneur
    user_submission = None
    if current_user.user_type.value == "entrepreneur":
        entrepreneur = get_entrepreneur_by_user_id(db, current_user.user_id)
        if entrepreneur:
            submissions = get_user_submissions(db, entrepreneur.entrepreneur_id, assignment_id)
            user_submission = submissions[0] if submissions else None
    
    return AssignmentResponse(**format_assignment_response(assignment, current_user.user_id, user_submission))

@router.put("/{assignment_id}", response_model=AssignmentResponse)
def update_assignment_route(
    assignment_id: UUID,
    update_data: AssignmentUpdate,
    current_user: User = Depends(require_expert),
    db: Session = Depends(get_db)
):
    """✏️ Modifier un devoir"""
    
    assignment = update_assignment(db, assignment_id, update_data, current_user.user_id)
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Devoir non trouvé ou non autorisé"
        )
    
    return AssignmentResponse(**format_assignment_response(assignment, current_user.user_id))

@router.delete("/{assignment_id}")
def delete_assignment_route(
    assignment_id: UUID,
    current_user: User = Depends(require_expert),
    db: Session = Depends(get_db)
):
    """🗑️ Supprimer un devoir"""
    
    success = delete_assignment(db, assignment_id, current_user.user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Devoir non trouvé ou non autorisé"
        )
    
    return {"message": "Devoir supprimé avec succès"}

@router.post("/{assignment_id}/publish", response_model=AssignmentResponse)
def publish_assignment_route(
    assignment_id: UUID,
    current_user: User = Depends(require_expert),
    db: Session = Depends(get_db)
):
    """📢 Publier un devoir"""
    
    assignment = publish_assignment(db, assignment_id, current_user.user_id)
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Devoir non trouvé ou non autorisé"
        )
    
    return AssignmentResponse(**format_assignment_response(assignment, current_user.user_id))

# ========== ROUTES SOUMISSIONS ==========

@router.post("/{assignment_id}/submit", response_model=AssignmentSubmissionResponse)
async def submit_assignment_work(
    assignment_id: UUID,
    submission_text: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None),
    current_user: User = Depends(require_entrepreneur),
    db: Session = Depends(get_db)
):
    """📤 Soumettre un devoir avec fichiers"""
    
    entrepreneur = get_entrepreneur_by_user_id(db, current_user.user_id)
    if not entrepreneur:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil entrepreneur non trouvé"
        )
    
    # Upload des fichiers si présents
    file_urls = []
    if files:
        for file in files:
            if file.filename:
                # Vérifications
                if file.size > 10 * 1024 * 1024:  # 10MB max par fichier
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Fichier {file.filename} trop volumineux (max 10MB)"
                    )
                
                try:
                    file_content = await file.read()
                    content_type = get_content_type(file.filename)
                    
                    upload_result = storage.upload_file(
                        bucket_name="documents",
                        file_content=file_content,
                        file_name=file.filename,
                        content_type=content_type,
                        folder=f"assignments/{assignment_id}/{entrepreneur.entrepreneur_id}"
                    )
                    
                    if upload_result['success']:
                        file_urls.append(upload_result['url'])
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Erreur upload {file.filename}: {upload_result['error']}"
                        )
                        
                except Exception as e:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Erreur traitement {file.filename}: {str(e)}"
                    )
    
    # Créer soumission
    submission_data = AssignmentSubmissionCreate(
        assignment_id=assignment_id,
        submission_text=submission_text,
        submission_files=file_urls
    )
    
    submission = create_or_update_submission(
        db, submission_data, entrepreneur.entrepreneur_id,
        ip_address="127.0.0.1"  # TODO: Récupérer vraie IP
    )
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de créer la soumission (limite de tentatives atteinte ou devoir non disponible)"
        )
    
    return AssignmentSubmissionResponse(**format_submission_response(submission, current_user.user_id))

@router.post("/submissions/{submission_id}/submit-final")
def submit_final_assignment(
    submission_id: UUID,
    time_spent: Optional[int] = Query(None, description="Temps passé en minutes"),
    current_user: User = Depends(require_entrepreneur),
    db: Session = Depends(get_db)
):
    """✅ Soumettre définitivement (passer de brouillon à soumis)"""
    
    entrepreneur = get_entrepreneur_by_user_id(db, current_user.user_id)
    if not entrepreneur:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil entrepreneur non trouvé"
        )
    
    submission = submit_assignment(db, submission_id, entrepreneur.entrepreneur_id, time_spent)
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Soumission non trouvée ou non modifiable"
        )
    
    return {"message": "Devoir soumis avec succès", "submission_id": str(submission.submission_id)}

@router.get("/submissions/{submission_id}", response_model=AssignmentSubmissionResponse)
def get_submission_details(
   submission_id: UUID,
   current_user: User = Depends(get_current_user),
   db: Session = Depends(get_db)
):
   """📄 Détails d'une soumission"""
   
   submission = get_submission_by_id(db, submission_id, current_user.user_id)
   
   if not submission:
       raise HTTPException(
           status_code=status.HTTP_404_NOT_FOUND,
           detail="Soumission non trouvée ou non autorisée"
       )
   
   return AssignmentSubmissionResponse(**format_submission_response(submission, current_user.user_id))

@router.put("/submissions/{submission_id}", response_model=AssignmentSubmissionResponse)
def update_submission_draft(
   submission_id: UUID,
   update_data: AssignmentSubmissionUpdate,
   current_user: User = Depends(require_entrepreneur),
   db: Session = Depends(get_db)
):
   """✏️ Modifier brouillon de soumission"""
   
   # TODO: Implémenter mise à jour de soumission
   # Pour l'instant, retourner erreur
   raise HTTPException(
       status_code=status.HTTP_501_NOT_IMPLEMENTED,
       detail="Modification de soumission pas encore implémentée"
   )

# ========== ROUTES ÉVALUATION (EXPERTS) ==========

@router.get("/grading/pending", response_model=List[AssignmentSubmissionResponse])
def get_pending_submissions(
   assignment_id: Optional[UUID] = Query(None, description="Filtrer par devoir"),
   current_user: User = Depends(require_expert),
   db: Session = Depends(get_db)
):
   """📋 Soumissions en attente d'évaluation (Expert)"""
   
   expert = get_expert_by_user_id(db, current_user.user_id)
   if not expert:
       raise HTTPException(
           status_code=status.HTTP_404_NOT_FOUND,
           detail="Profil expert non trouvé"
       )
   
   submissions = get_submissions_for_grading(
       db, expert_id=expert.expert_id, assignment_id=assignment_id
   )
   
   return [
       AssignmentSubmissionResponse(**format_submission_response(submission, current_user.user_id))
       for submission in submissions
   ]

@router.post("/submissions/{submission_id}/grade", response_model=GradeSubmissionResponse)
def grade_assignment_submission(
   submission_id: UUID,
   grade_data: GradeSubmissionRequest,
   current_user: User = Depends(require_expert),
   db: Session = Depends(get_db)
):
   """📊 Évaluer une soumission (Expert)"""
   
   expert = get_expert_by_user_id(db, current_user.user_id)
   if not expert:
       raise HTTPException(
           status_code=status.HTTP_404_NOT_FOUND,
           detail="Profil expert non trouvé"
       )
   
   submission = grade_submission(db, submission_id, grade_data, expert.expert_id)
   
   if not submission:
       raise HTTPException(
           status_code=status.HTTP_404_NOT_FOUND,
           detail="Soumission non trouvée ou non évaluable"
       )
   
   return GradeSubmissionResponse(
       submission_id=submission.submission_id,
       score=submission.score,
       grade=submission.grade,
       feedback=submission.feedback,
       graded_by=submission.graded_by,
       graded_at=submission.graded_at
   )

# ========== ROUTES LISTES ET FILTRES ==========

@router.get("/module/{module_id}", response_model=List[AssignmentResponse])
def get_module_assignments(
   module_id: UUID,
   published_only: bool = Query(True, description="Afficher seulement les devoirs publiés"),
   current_user: User = Depends(get_current_user),
   db: Session = Depends(get_db)
):
   """📋 Devoirs d'un module"""
   
   assignments = get_assignments_by_module(db, module_id, published_only)
   
   return [
       AssignmentResponse(**format_assignment_response(assignment, current_user.user_id))
       for assignment in assignments
   ]

@router.get("/entrepreneur/available", response_model=List[AssignmentListItem])
def get_available_assignments(
   program_id: Optional[UUID] = Query(None, description="Filtrer par programme"),
   include_completed: bool = Query(True, description="Inclure les devoirs terminés"),
   current_user: User = Depends(require_entrepreneur),
   db: Session = Depends(get_db)
):
   """📝 Mes devoirs disponibles (Entrepreneur)"""
   
   entrepreneur = get_entrepreneur_by_user_id(db, current_user.user_id)
   if not entrepreneur:
       raise HTTPException(
           status_code=status.HTTP_404_NOT_FOUND,
           detail="Profil entrepreneur non trouvé"
       )
   
   assignments_data = get_assignments_for_entrepreneur(
       db, entrepreneur.entrepreneur_id, program_id, include_completed
   )
   
   result = []
   for item in assignments_data:
       assignment = item["assignment"]
       user_submission = item["user_submission"]
       
       result.append(AssignmentListItem(
           assignment_id=assignment.assignment_id,
           title=assignment.title,
           assignment_type=assignment.assignment_type,
           due_date=assignment.due_date,
           max_score=assignment.max_score,
           status=assignment.status,
           is_available=item["is_available"],
           is_overdue=item["is_overdue"],
           user_submitted=user_submission is not None and user_submission.status.value == "submitted",
           user_score=user_submission.score if user_submission else None
       ))
   
   return result

@router.get("/entrepreneur/submissions", response_model=SubmissionSummary)
def get_my_submissions(
   program_id: Optional[UUID] = Query(None, description="Filtrer par programme"),
   current_user: User = Depends(require_entrepreneur),
   db: Session = Depends(get_db)
):
   """📊 Résumé de mes soumissions (Entrepreneur)"""
   
   entrepreneur = get_entrepreneur_by_user_id(db, current_user.user_id)
   if not entrepreneur:
       raise HTTPException(
           status_code=status.HTTP_404_NOT_FOUND,
           detail="Profil entrepreneur non trouvé"
       )
   
   summary_data = get_entrepreneur_assignment_summary(db, entrepreneur.entrepreneur_id, program_id)
   
   submissions = [
       AssignmentSubmissionResponse(**format_submission_response(submission, current_user.user_id))
       for submission in summary_data["submissions"]
   ]
   
   return SubmissionSummary(
       total_assignments=summary_data["total_assignments"],
       completed_assignments=summary_data["completed_assignments"],
       pending_assignments=summary_data["pending_assignments"],
       overdue_assignments=summary_data["overdue_assignments"],
       average_score=summary_data["average_score"],
       submissions=submissions
   )

@router.get("/expert/my-assignments", response_model=List[AssignmentResponse])
def get_my_expert_assignments(
   current_user: User = Depends(require_expert),
   db: Session = Depends(get_db)
):
   """📚 Mes devoirs créés (Expert)"""
   
   expert = get_expert_by_user_id(db, current_user.user_id)
   if not expert:
       raise HTTPException(
           status_code=status.HTTP_404_NOT_FOUND,
           detail="Profil expert non trouvé"
       )
   
   assignments = get_assignments_by_expert(db, expert.expert_id)
   
   return [
       AssignmentResponse(**format_assignment_response(assignment, current_user.user_id))
       for assignment in assignments
   ]

# ========== RECHERCHE ET STATISTIQUES ==========

@router.get("/search", response_model=List[AssignmentResponse])
def search_assignments_route(
   query: str = Query(..., description="Terme de recherche"),
   assignment_type: Optional[str] = Query(None),
   module_id: Optional[UUID] = Query(None),
   limit: int = Query(20),
   current_user: User = Depends(get_current_user),
   db: Session = Depends(get_db)
):
   """🔍 Rechercher devoirs"""
   
   assignments = search_assignments(db, query, assignment_type, module_id, None, limit)
   
   return [
       AssignmentResponse(**format_assignment_response(assignment, current_user.user_id))
       for assignment in assignments
   ]

@router.get("/{assignment_id}/stats", response_model=AssignmentStats)
def get_assignment_statistics(
   assignment_id: UUID,
   current_user: User = Depends(require_expert),
   db: Session = Depends(get_db)
):
   """📊 Statistiques d'un devoir (Expert)"""
   
   stats = get_assignment_stats(db, assignment_id)
   return AssignmentStats(**stats)

# ========== ROUTES UTILITAIRES ==========

@router.get("/types")
def get_assignment_types():
   """📋 Types de devoirs disponibles"""
   from app.models.assignment import AssignmentType
   
   return {
       "assignment_types": [
           {
               "value": type.value,
               "label": type.value.title(),
               "description": _get_type_description(type.value)
           } for type in AssignmentType
       ]
   }

@router.get("/statuses")
def get_assignment_statuses():
   """📋 Statuts de devoirs disponibles"""
   from app.models.assignment import AssignmentStatus
   
   return {
       "assignment_statuses": [
           {
               "value": status.value,
               "label": status.value.title(),
               "description": _get_status_description(status.value)
           } for status in AssignmentStatus
       ]
   }

def _get_type_description(assignment_type: str) -> str:
   """Descriptions des types de devoirs"""
   descriptions = {
       "quiz": "Quiz à choix multiples ou questions courtes",
       "essay": "Rédaction d'un essai ou rapport détaillé",
       "project": "Projet pratique avec livrables",
       "presentation": "Présentation orale ou vidéo",
       "practical": "Exercice pratique ou étude de cas",
       "peer_review": "Évaluation par les pairs"
   }
   return descriptions.get(assignment_type, "Type de devoir")

def _get_status_description(status: str) -> str:
   """Descriptions des statuts"""
   descriptions = {
       "draft": "Brouillon - Non visible par les étudiants",
       "published": "Publié - Accessible aux étudiants",
       "closed": "Fermé - Plus de soumissions acceptées"
   }
   return descriptions.get(status, "Statut")