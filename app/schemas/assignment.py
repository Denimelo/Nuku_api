from pydantic import BaseModel, UUID4
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from enum import Enum

class AssignmentType(str, Enum):
    quiz = "quiz"
    essay = "essay"
    project = "project"
    presentation = "presentation"
    practical = "practical"
    peer_review = "peer_review"

class AssignmentStatus(str, Enum):
    draft = "draft"
    published = "published"
    closed = "closed"

class SubmissionStatus(str, Enum):
    draft = "draft"
    submitted = "submitted"
    graded = "graded"
    returned = "returned"

# Schémas Assignment
class AssignmentBase(BaseModel):
    title: str
    description: str
    instructions: Optional[str] = None
    assignment_type: AssignmentType
    max_score: float = 100.0
    passing_score: float = 60.0
    due_date: Optional[datetime] = None
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None
    max_attempts: int = 1
    time_limit_minutes: Optional[int] = None
    is_graded: bool = True
    allow_late_submission: bool = False

class AssignmentCreate(AssignmentBase):
    module_id: UUID4

class AssignmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None
    assignment_type: Optional[AssignmentType] = None
    max_score: Optional[float] = None
    passing_score: Optional[float] = None
    due_date: Optional[datetime] = None
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None
    max_attempts: Optional[int] = None
    time_limit_minutes: Optional[int] = None
    status: Optional[AssignmentStatus] = None
    is_graded: Optional[bool] = None
    allow_late_submission: Optional[bool] = None

class AssignmentResponse(AssignmentBase):
    assignment_id: UUID4
    module_id: UUID4
    created_by: UUID4
    status: AssignmentStatus
    created_at: datetime
    updated_at: datetime
    submission_count: int
    average_score: float
    
    # Données enrichies
    creator_name: Optional[str] = None
    module_title: Optional[str] = None
    is_available: bool = True
    is_overdue: bool = False
    time_remaining_hours: Optional[float] = None
    
    # Progression utilisateur
    user_submission: Optional['AssignmentSubmissionResponse'] = None
    user_attempts_used: int = 0
    user_can_submit: bool = True

    class Config:
        from_attributes = True

# Schémas AssignmentSubmission
class AssignmentSubmissionBase(BaseModel):
    submission_text: Optional[str] = None
    submission_files: Optional[List[str]] = []

class AssignmentSubmissionCreate(AssignmentSubmissionBase):
    assignment_id: UUID4

class AssignmentSubmissionUpdate(BaseModel):
    submission_text: Optional[str] = None
    submission_files: Optional[List[str]] = None
    time_spent_minutes: Optional[int] = None

class AssignmentSubmissionResponse(AssignmentSubmissionBase):
    submission_id: UUID4
    assignment_id: UUID4
    entrepreneur_id: UUID4
    status: SubmissionStatus
    attempt_number: int
    score: Optional[float] = None
    grade: Optional[str] = None
    feedback: Optional[str] = None
    graded_by: Optional[UUID4] = None
    submitted_at: Optional[datetime] = None
    graded_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    time_spent_minutes: Optional[int] = None
    
    # Données enrichies
    assignment_title: Optional[str] = None
    grader_name: Optional[str] = None
    is_late: bool = False
    is_passing: bool = False
    grade_percentage: float = 0.0

    class Config:
        from_attributes = True

# Schémas pour l'évaluation
class GradeSubmissionRequest(BaseModel):
    score: float
    grade: Optional[str] = None
    feedback: Optional[str] = None

class GradeSubmissionResponse(BaseModel):
    submission_id: UUID4
    score: float
    grade: Optional[str] = None
    feedback: Optional[str] = None
    graded_by: UUID4
    graded_at: datetime

# Schémas de statistiques
class AssignmentStats(BaseModel):
    total_submissions: int
    graded_submissions: int
    pending_submissions: int
    average_score: float
    passing_rate: float
    on_time_submissions: int
    late_submissions: int
    completion_rate: float

class SubmissionSummary(BaseModel):
    """Résumé des soumissions pour un entrepreneur"""
    total_assignments: int
    completed_assignments: int
    pending_assignments: int
    overdue_assignments: int
    average_score: float
    submissions: List[AssignmentSubmissionResponse]

# Schémas pour les listes et filtres
class AssignmentFilter(BaseModel):
    module_id: Optional[UUID4] = None
    assignment_type: Optional[AssignmentType] = None
    status: Optional[AssignmentStatus] = None
    is_overdue: Optional[bool] = None
    has_submissions: Optional[bool] = None

class AssignmentListItem(BaseModel):
    """Item simplifié pour les listes"""
    assignment_id: UUID4
    title: str
    assignment_type: AssignmentType
    due_date: Optional[datetime] = None
    max_score: float
    status: AssignmentStatus
    is_available: bool
    is_overdue: bool
    user_submitted: bool = False
    user_score: Optional[float] = None