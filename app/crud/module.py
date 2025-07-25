from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, asc, func
from uuid import UUID
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.models.module import Module, ModuleType, ModuleDifficulty, ModuleStatus
from app.models.moduleContent import ModuleContent, ContentType
from app.models.moduleProgress import ModuleProgress
from app.models.expert import Expert
from app.models.program import Program
from app.schemas.module import ModuleCreate, ModuleUpdate, ModuleContentCreate, ModuleContentUpdate

# ========== CRUD MODULE ==========

def create_module(db: Session, module_data: ModuleCreate, created_by: UUID) -> Module:
    """Créer un nouveau module"""
    
    module = Module(
        **module_data.dict(),
        created_by=created_by
    )
    
    db.add(module)
    db.commit()
    db.refresh(module)
    return module

def get_module_by_id(db: Session, module_id: UUID) -> Optional[Module]:
    """Récupérer module par ID avec relations"""
    return db.query(Module).options(
        joinedload(Module.created_by_expert).joinedload(Expert.user),
        joinedload(Module.program),
        joinedload(Module.contents),
        joinedload(Module.assignments)
    ).filter(Module.module_id == module_id).first()

def get_modules_by_program(
    db: Session, 
    program_id: UUID,
    published_only: bool = True
) -> List[Module]:
    """Récupérer modules d'un programme"""
    query = db.query(Module).options(
        joinedload(Module.created_by_expert).joinedload(Expert.user),
        joinedload(Module.contents)
    ).filter(Module.program_id == program_id)
    
    if published_only:
        query = query.filter(
            Module.status == ModuleStatus.published,
            Module.is_visible == True
        )
    
    return query.order_by(Module.order_index).all()

def get_modules_by_expert(db: Session, expert_id: UUID) -> List[Module]:
    """Modules créés par un expert"""
    return db.query(Module).options(
        joinedload(Module.program),
        joinedload(Module.contents)
    ).filter(Module.created_by == expert_id).order_by(desc(Module.created_at)).all()

def update_module(
    db: Session, 
    module_id: UUID, 
    update_data: ModuleUpdate,
    user_id: UUID
) -> Optional[Module]:
    """Mettre à jour module (seul le créateur ou admin)"""
    module = db.query(Module).filter(Module.module_id == module_id).first()
    
    if not module:
        return None
    
    # TODO: Vérifier permissions (créateur ou admin)
    
    for field, value in update_data.dict(exclude_unset=True).items():
        if hasattr(module, field):
            setattr(module, field, value)
    
    module.updated_at = datetime.utcnow()
    
    # Si publication, marquer date
    if update_data.status == ModuleStatus.published and not module.published_at:
        module.published_at = datetime.utcnow()
    
    db.commit()
    db.refresh(module)
    return module

def delete_module(db: Session, module_id: UUID, user_id: UUID) -> bool:
    """Supprimer module"""
    module = db.query(Module).filter(Module.module_id == module_id).first()
    
    if not module:
        return False
    
    # TODO: Vérifier permissions
    
    db.delete(module)
    db.commit()
    return True

def publish_module(db: Session, module_id: UUID, user_id: UUID) -> Optional[Module]:
    """Publier un module"""
    module = db.query(Module).filter(Module.module_id == module_id).first()
    
    if not module:
        return None
    
    module.status = ModuleStatus.published
    module.published_at = datetime.utcnow()
    module.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(module)
    return module

# ========== CRUD MODULE CONTENT ==========

def create_module_content(
    db: Session, 
    content_data: ModuleContentCreate,
    file_info: Optional[Dict[str, Any]] = None
) -> ModuleContent:
    """Créer contenu de module"""
    
    content_dict = content_data.dict()
    
    # Ajouter infos fichier si présent
    if file_info:
        content_dict.update(file_info)
    
    content = ModuleContent(**content_dict)
    
    db.add(content)
    db.commit()
    db.refresh(content)
    
    # Mettre à jour compteur du module
    _update_module_stats(db, content_data.module_id)
    
    return content

def get_module_contents(
    db: Session, 
    module_id: UUID,
    visible_only: bool = True
) -> List[ModuleContent]:
    """Récupérer contenus d'un module"""
    query = db.query(ModuleContent).filter(ModuleContent.module_id == module_id)
    
    if visible_only:
        query = query.filter(ModuleContent.is_visible == True)
    
    return query.order_by(ModuleContent.order_index).all()

def update_module_content(
    db: Session,
    content_id: UUID,
    update_data: ModuleContentUpdate,
    file_info: Optional[Dict[str, Any]] = None
) -> Optional[ModuleContent]:
    """Mettre à jour contenu"""
    content = db.query(ModuleContent).filter(ModuleContent.content_id == content_id).first()
    
    if not content:
        return None
    
    for field, value in update_data.dict(exclude_unset=True).items():
        if hasattr(content, field):
            setattr(content, field, value)
    
    # Ajouter infos fichier si présent
    if file_info:
        for field, value in file_info.items():
            if hasattr(content, field):
                setattr(content, field, value)
    
    content.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(content)
    return content

def delete_module_content(db: Session, content_id: UUID) -> bool:
    """Supprimer contenu"""
    content = db.query(ModuleContent).filter(ModuleContent.content_id == content_id).first()
    
    if not content:
        return False
    
    module_id = content.module_id
    
    db.delete(content)
    db.commit()
    
    # Mettre à jour stats module
    _update_module_stats(db, module_id)
    
    return True

def reorder_module_contents(
    db: Session,
    module_id: UUID,
    content_orders: List[Dict[str, Any]]  # [{"content_id": "...", "order_index": 1}]
) -> bool:
    """Réorganiser l'ordre des contenus"""
    
    for item in content_orders:
        content = db.query(ModuleContent).filter(
            ModuleContent.content_id == item["content_id"],
            ModuleContent.module_id == module_id
        ).first()
        
        if content:
            content.order_index = item["order_index"]
    
    db.commit()
    return True

# ========== CRUD PROGRESSION ==========

def get_or_create_module_progress(
    db: Session,
    module_id: UUID,
    entrepreneur_id: UUID
) -> ModuleProgress:
    """Récupérer ou créer progression d'un module"""
    
    progress = db.query(ModuleProgress).filter(
        ModuleProgress.module_id == module_id,
        ModuleProgress.entrepreneur_id == entrepreneur_id
    ).first()
    
    if not progress:
        # Compter contenus du module
        total_contents = db.query(ModuleContent).filter(
            ModuleContent.module_id == module_id,
            ModuleContent.is_visible == True
        ).count()
        
        progress = ModuleProgress(
            module_id=module_id,
            entrepreneur_id=entrepreneur_id,
            total_contents=total_contents
        )
        
        db.add(progress)
        db.commit()
        db.refresh(progress)
    
    return progress

def update_module_progress(
    db: Session,
    module_id: UUID,
    entrepreneur_id: UUID,
    content_id: Optional[UUID] = None,
    time_spent: Optional[int] = None
) -> ModuleProgress:
    """Mettre à jour progression"""
    
    progress = get_or_create_module_progress(db, module_id, entrepreneur_id)
    
    # Marquer comme commencé si pas encore fait
    if not progress.is_started:
        progress.is_started = True
        progress.started_at = datetime.utcnow()
    
    # Mettre à jour dernier contenu consulté
    if content_id:
        progress.last_content_id = content_id
    
    # Ajouter temps passé
    if time_spent:
        progress.time_spent_minutes += time_spent
    
    progress.last_accessed_at = datetime.utcnow()
    
    # Recalculer progression
    _recalculate_progress(db, progress)
    
    db.commit()
    db.refresh(progress)
    return progress

def mark_content_completed(
    db: Session,
    module_id: UUID,
    entrepreneur_id: UUID,
    content_id: UUID
) -> ModuleProgress:
    """Marquer un contenu comme complété"""
    
    progress = get_or_create_module_progress(db, module_id, entrepreneur_id)
    
    # TODO: Tracking des contenus complétés individuellement
    # Pour l'instant, incrémenter le compteur
    if progress.contents_completed < progress.total_contents:
        progress.contents_completed += 1
        
        # Recalculer pourcentage
        _recalculate_progress(db, progress)
    
    db.commit()
    db.refresh(progress)
    return progress

def get_user_module_progress(
    db: Session,
    entrepreneur_id: UUID,
    program_id: Optional[UUID] = None
) -> List[ModuleProgress]:
    """Progression de l'utilisateur sur les modules"""
    
    query = db.query(ModuleProgress).options(
        joinedload(ModuleProgress.module)
    ).filter(ModuleProgress.entrepreneur_id == entrepreneur_id)
    
    if program_id:
        query = query.join(Module).filter(Module.program_id == program_id)
    
    return query.all()

# ========== STATISTIQUES ==========

def get_module_stats(db: Session, module_id: UUID) -> Dict[str, Any]:
    """Statistiques d'un module"""
    
    # Nombre d'inscriptions (via participation aux programmes)
    enrollments = db.query(ModuleProgress).filter(
        ModuleProgress.module_id == module_id
    ).count()
    
    # Taux de completion
    completed = db.query(ModuleProgress).filter(
        ModuleProgress.module_id == module_id,
        ModuleProgress.is_completed == True
    ).count()
    
    completion_rate = (completed / enrollments * 100) if enrollments > 0 else 0
    
    # Temps moyen passé
    avg_time = db.query(func.avg(ModuleProgress.time_spent_minutes)).filter(
        ModuleProgress.module_id == module_id,
        ModuleProgress.time_spent_minutes > 0
    ).scalar() or 0
    
    return {
        "total_enrollments": enrollments,
        "completion_rate": round(completion_rate, 2),
        "average_time_spent": round(avg_time, 2),
        "average_score": 0.0,  # TODO: Calculer depuis assignments
        "content_engagement": {},  # TODO: Implémenter
        "difficulty_feedback": {}  # TODO: Implémenter
    }

def get_program_learning_stats(
    db: Session,
    program_id: UUID
) -> Dict[str, Any]:
    """Statistiques d'apprentissage d'un programme"""
    
    modules = get_modules_by_program(db, program_id, published_only=False)
    
    total_modules = len(modules)
    total_contents = sum(len(module.contents) for module in modules)
    
    # Progression moyenne
    avg_progress = db.query(func.avg(ModuleProgress.completion_percentage)).join(Module).filter(
        Module.program_id == program_id
    ).scalar() or 0
    
    return {
        "total_modules": total_modules,
        "total_contents": total_contents,
        "average_progress": round(avg_progress, 2),
        "modules_published": len([m for m in modules if m.status == ModuleStatus.published])
    }

# ========== FONCTIONS UTILITAIRES ==========

def _update_module_stats(db: Session, module_id: UUID):
    """Mettre à jour statistiques du module"""
    module = db.query(Module).filter(Module.module_id == module_id).first()
    
    if module:
        # Recalculer nombre de contenus
        content_count = db.query(ModuleContent).filter(
            ModuleContent.module_id == module_id
        ).count()
        
        # TODO: Mettre à jour d'autres stats si nécessaire
        
        db.commit()

def _recalculate_progress(db: Session, progress: ModuleProgress):
    """Recalculer pourcentage de progression"""
    if progress.total_contents > 0:
        progress.completion_percentage = (progress.contents_completed / progress.total_contents) * 100
        
        # Marquer comme complété si 100%
        if progress.completion_percentage >= 100 and not progress.is_completed:
            progress.is_completed = True
            progress.completed_at = datetime.utcnow()

def search_modules(
    db: Session,
    query: str,
    module_type: Optional[ModuleType] = None,
    difficulty: Optional[ModuleDifficulty] = None,
    program_id: Optional[UUID] = None,
    limit: int = 20
) -> List[Module]:
    """Rechercher modules"""
    
    search_query = db.query(Module).options(
        joinedload(Module.created_by_expert).joinedload(Expert.user),
        joinedload(Module.program)
    ).filter(
        Module.status == ModuleStatus.published,
        Module.is_visible == True
    )
    
    if query:
        search_query = search_query.filter(
            or_(
                Module.title.ilike(f"%{query}%"),
                Module.description.ilike(f"%{query}%"),
                Module.learning_objectives.ilike(f"%{query}%")
            )
        )
    
    if module_type:
        search_query = search_query.filter(Module.module_type == module_type)
    
    if difficulty:
        search_query = search_query.filter(Module.difficulty_level == difficulty)
    
    if program_id:
        search_query = search_query.filter(Module.program_id == program_id)
    
    return search_query.order_by(desc(Module.created_at)).limit(limit).all()