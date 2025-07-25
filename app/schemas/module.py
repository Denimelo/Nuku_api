from pydantic import BaseModel, UUID4
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class ModuleType(str, Enum):
    lesson = "lesson"
    workshop = "workshop"
    assessment = "assessment"
    project = "project"
    discussion = "discussion"

class ModuleDifficulty(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"
    expert = "expert"

class ModuleStatus(str, Enum):
    draft = "draft"
    published = "published"
    archived = "archived"

class ContentType(str, Enum):
    text = "text"
    video = "video"
    audio = "audio"
    document = "document"
    interactive = "interactive"
    quiz = "quiz"
    link = "link"

# Schémas de base Module
class ModuleBase(BaseModel):
    title: str
    description: Optional[str] = None
    learning_objectives: Optional[str] = None
    module_type: ModuleType = ModuleType.lesson
    difficulty_level: ModuleDifficulty = ModuleDifficulty.beginner
    estimated_duration_minutes: Optional[int] = None
    is_mandatory: bool = True
    is_visible: bool = True
    prerequisite_modules: Optional[str] = None
    minimum_score_required: Optional[float] = None

class ModuleCreate(ModuleBase):
    program_id: UUID4
    order_index: Optional[int] = 0

class ModuleUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    learning_objectives: Optional[str] = None
    module_type: Optional[ModuleType] = None
    difficulty_level: Optional[ModuleDifficulty] = None
    estimated_duration_minutes: Optional[int] = None
    is_mandatory: Optional[bool] = None
    is_visible: Optional[bool] = None
    prerequisite_modules: Optional[str] = None
    minimum_score_required: Optional[float] = None
    order_index: Optional[int] = None
    status: Optional[ModuleStatus] = None

class ModuleResponse(ModuleBase):
    module_id: UUID4
    program_id: UUID4
    order_index: int
    status: ModuleStatus
    created_by: UUID4
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None
    view_count: int
    completion_count: int
    average_rating: float
    
    # Données enrichies
    creator_name: Optional[str] = None
    program_name: Optional[str] = None
    total_content_count: int = 0
    content_summary: List[Dict[str, Any]] = []
    
    # Progression utilisateur (si applicable)
    user_progress: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

# Schémas ModuleContent
class ModuleContentBase(BaseModel):
    title: str
    description: Optional[str] = None
    content_type: ContentType
    text_content: Optional[str] = None
    external_link: Optional[str] = None
    is_visible: bool = True
    is_downloadable: bool = False
    order_index: int = 0

class ModuleContentCreate(ModuleContentBase):
    module_id: UUID4

class ModuleContentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    text_content: Optional[str] = None
    external_link: Optional[str] = None
    is_visible: Optional[bool] = None
    is_downloadable: Optional[bool] = None
    order_index: Optional[int] = None

class ModuleContentResponse(ModuleContentBase):
    content_id: UUID4
    module_id: UUID4
    file_url: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    duration_seconds: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    # Propriétés calculées
    is_media: bool = False
    duration_formatted: str = "00:00"

    class Config:
        from_attributes = True

# Schémas pour la progression
class ModuleProgressBase(BaseModel):
    completion_percentage: float = 0.0
    contents_completed: int = 0
    total_contents: int = 0
    is_started: bool = False
    is_completed: bool = False

class ModuleProgressResponse(ModuleProgressBase):
    progress_id: UUID4
    module_id: UUID4
    entrepreneur_id: UUID4
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_accessed_at: datetime
    time_spent_minutes: int = 0
    last_content_id: Optional[UUID4] = None
    progress_status: str

    class Config:
        from_attributes = True

# Schémas enrichis
class ModuleWithProgress(ModuleResponse):
    """Module avec progression de l'utilisateur"""
    progress: Optional[ModuleProgressResponse] = None
    next_content: Optional[ModuleContentResponse] = None
    completed_contents: List[UUID4] = []

class ModuleSummary(BaseModel):
    """Résumé d'un module pour les listes"""
    module_id: UUID4
    title: str
    description: Optional[str] = None
    module_type: ModuleType
    difficulty_level: ModuleDifficulty
    estimated_duration_minutes: Optional[int] = None
    order_index: int
    status: ModuleStatus
    completion_percentage: float = 0.0
    is_available: bool = True
    is_completed: bool = False

class ModuleStats(BaseModel):
    """Statistiques d'un module"""
    total_enrollments: int
    completion_rate: float
    average_time_spent: float
    average_score: float
    content_engagement: Dict[str, float]
    difficulty_feedback: Dict[str, int]

class ModuleCatalog(BaseModel):
    """Catalogue de modules pour un programme"""
    program_id: UUID4
    program_name: str
    total_modules: int
    modules: List[ModuleSummary]
    user_overall_progress: float = 0.0
    estimated_total_duration: int = 0