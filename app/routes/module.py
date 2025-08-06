from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.auth.dependencies import get_current_user, require_expert, require_admin
from app.models.user import User
from app.schemas.module import (
    ModuleCreate, ModuleUpdate, ModuleResponse, ModuleWithProgress,
    ModuleSummary, ModuleStats, ModuleCatalog, ModuleContentCreate,
    ModuleContentUpdate, ModuleContentResponse, ModuleProgressResponse
)
from app.crud.module import (
    create_module, get_module_by_id, get_modules_by_program, get_modules_by_expert,
    update_module, delete_module, publish_module, create_module_content,
    get_module_contents, update_module_content, delete_module_content,
    reorder_module_contents, get_or_create_module_progress, update_module_progress,
    mark_content_completed, get_user_module_progress, get_module_stats,
    get_program_learning_stats, search_modules
)
from app.crud.expert import get_expert_by_user_id
from app.crud.entrepreneur import get_entrepreneur_by_user_id
from app.crud.program import get_program
from app.utils.supabase_storage import storage, get_content_type, is_image, is_document

router = APIRouter(prefix="/modules", tags=["Modules"])

def format_module_response(module, current_user_id: UUID, include_progress: bool = False) -> dict:
    """Formater réponse module"""
    
    # Données de base
    module_data = {
        "module_id": module.module_id,
        "program_id": module.program_id,
        "title": module.title,
        "description": module.description,
        "learning_objectives": module.learning_objectives,
        "module_type": module.module_type,
        "difficulty_level": module.difficulty_level,
        "estimated_duration_minutes": module.estimated_duration_minutes,
        "order_index": module.order_index,
        "status": module.status,
        "is_mandatory": module.is_mandatory,
        "is_visible": module.is_visible,
        "prerequisite_modules": module.prerequisite_modules,
        "minimum_score_required": module.minimum_score_required,
        "created_by": module.created_by,
        "created_at": module.created_at,
        "updated_at": module.updated_at,
        "published_at": module.published_at,
        "view_count": module.view_count,
        "completion_count": module.completion_count,
        "average_rating": module.average_rating,
        "creator_name": f"{module.created_by_expert.user.first_name} {module.created_by_expert.user.last_name}" if module.created_by_expert and module.created_by_expert.user else None,
        "program_name": module.program.name if module.program else None,
        "total_content_count": len(module.contents) if module.contents else 0,
        "content_summary": [
            {
                "content_id": str(content.content_id),
                "title": content.title,
                "content_type": content.content_type.value,
                "duration_seconds": content.duration_seconds,
                "order_index": content.order_index
            } for content in (module.contents or [])
        ]
    }
    
    return module_data

# ========== ROUTES MODULES ==========

@router.post("/", response_model=ModuleResponse)
def create_new_module(
    module_data: ModuleCreate,
    current_user: User = Depends(require_expert),
    db: Session = Depends(get_db)
):
    """📚 Créer un nouveau module (Expert)"""
    
    # Vérifier que le programme existe
    program = get_program(db, module_data.program_id)
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Programme non trouvé"
        )
    
    # Récupérer expert ID
    expert = get_expert_by_user_id(db, current_user.user_id)
    if not expert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil expert non trouvé"
        )
    
    module = create_module(db, module_data, expert.expert_id)
    
    return ModuleResponse(**format_module_response(module, current_user.user_id))

@router.get("/{module_id}", response_model=ModuleWithProgress)
def get_module_details(
    module_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """📖 Détails d'un module"""
    
    module = get_module_by_id(db, module_id)
    
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module non trouvé"
        )
    
    # Incrémenter compteur de vues
    module.view_count += 1
    db.commit()
    
    module_data = format_module_response(module, current_user.user_id)
    
    # Ajouter progression si entrepreneur
    progress = None
    next_content = None
    completed_contents = []
    
    if current_user.user_type.value == "entrepreneur":
        entrepreneur = get_entrepreneur_by_user_id(db, current_user.user_id)
        if entrepreneur:
            progress_obj = get_or_create_module_progress(db, module_id, entrepreneur.entrepreneur_id)
            
            progress = {
                "progress_id": progress_obj.progress_id,
                "module_id": progress_obj.module_id,
                "entrepreneur_id": progress_obj.entrepreneur_id,
                "completion_percentage": progress_obj.completion_percentage,
                "contents_completed": progress_obj.contents_completed,
                "total_contents": progress_obj.total_contents,
                "is_started": progress_obj.is_started,
                "is_completed": progress_obj.is_completed,
                "started_at": progress_obj.started_at,
                "completed_at": progress_obj.completed_at,
                "last_accessed_at": progress_obj.last_accessed_at,
                "time_spent_minutes": progress_obj.time_spent_minutes,
                "last_content_id": progress_obj.last_content_id,
                "progress_status": progress_obj.progress_status
            }
            
            # TODO: Déterminer prochain contenu et contenus complétés
    
    return ModuleWithProgress(
        **module_data,
        progress=progress,
        next_content=next_content,
        completed_contents=completed_contents
    )

@router.put("/{module_id}", response_model=ModuleResponse)
def update_module_route(
    module_id: UUID,
    update_data: ModuleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """✏️ Modifier un module"""
    
    module = update_module(db, module_id, update_data, current_user.user_id)
    
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module non trouvé ou non autorisé"
        )
    
    return ModuleResponse(**format_module_response(module, current_user.user_id))

@router.delete("/{module_id}")
def delete_module_route(
    module_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """🗑️ Supprimer un module"""
    
    success = delete_module(db, module_id, current_user.user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module non trouvé ou non autorisé"
        )
    
    return {"message": "Module supprimé avec succès"}

@router.post("/{module_id}/publish", response_model=ModuleResponse)
def publish_module_route(
    module_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """📢 Publier un module"""
    
    module = publish_module(db, module_id, current_user.user_id)
    
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module non trouvé ou non autorisé"
        )
    
    return ModuleResponse(**format_module_response(module, current_user.user_id))

@router.get("/program/{program_id}", response_model=ModuleCatalog)
def get_program_modules(
    program_id: UUID,
    published_only: bool = Query(True, description="Afficher seulement les modules publiés"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """📋 Modules d'un programme"""
    
    # Vérifier que le programme existe
    program = get_program(db, program_id)
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Programme non trouvé"
        )
    
    modules = get_modules_by_program(db, program_id, published_only)
    
    # Récupérer progression si entrepreneur
    user_progress = 0.0
    if current_user.user_type.value == "entrepreneur":
        entrepreneur = get_entrepreneur_by_user_id(db, current_user.user_id)
        if entrepreneur:
            progress_list = get_user_module_progress(db, entrepreneur.entrepreneur_id, program_id)
            if progress_list:
                user_progress = sum(p.completion_percentage for p in progress_list) / len(progress_list)
    
    # Formater modules
    module_summaries = []
    total_duration = 0
    
    for module in modules:
        # Progression individuelle
        completion = 0.0
        is_completed = False
        is_available = module.status.value == "published" and module.is_visible
        
        if current_user.user_type.value == "entrepreneur":
            entrepreneur = get_entrepreneur_by_user_id(db, current_user.user_id)
            if entrepreneur:
                progress = get_or_create_module_progress(db, module.module_id, entrepreneur.entrepreneur_id)
                completion = progress.completion_percentage
                is_completed = progress.is_completed
        
        module_summaries.append(ModuleSummary(
            module_id=module.module_id,
            title=module.title,
            description=module.description,
            module_type=module.module_type,
            difficulty_level=module.difficulty_level,
            estimated_duration_minutes=module.estimated_duration_minutes,
            order_index=module.order_index,
            status=module.status,
            completion_percentage=completion,
            is_available=is_available,
            is_completed=is_completed
        ))
        
        if module.estimated_duration_minutes:
            total_duration += module.estimated_duration_minutes
    
    return ModuleCatalog(
        program_id=program_id,
        program_name=program.name,
        total_modules=len(modules),
        modules=module_summaries,
        user_overall_progress=user_progress,
        estimated_total_duration=total_duration
    )

# ========== ROUTES CONTENUS ==========

@router.post("/{module_id}/contents", response_model=ModuleContentResponse)
async def create_module_content_route(
   module_id: UUID,
   title: str = Form(...),
   description: Optional[str] = Form(None),
   content_type: str = Form(...),
   text_content: Optional[str] = Form(None),
   external_link: Optional[str] = Form(None),
   order_index: int = Form(0),
   is_visible: bool = Form(True),
   is_downloadable: bool = Form(False),
   file: Optional[UploadFile] = File(None),
   current_user: User = Depends(require_expert),
   db: Session = Depends(get_db)
):
   """📎 Ajouter contenu à un module"""
   
   # Vérifier que le module existe
   module = get_module_by_id(db, module_id)
   if not module:
       raise HTTPException(
           status_code=status.HTTP_404_NOT_FOUND,
           detail="Module non trouvé"
       )
   
   # TODO: Vérifier permissions (créateur du module ou admin)
   
   # Préparer données de contenu
   content_data = ModuleContentCreate(
       module_id=module_id,
       title=title,
       description=description,
       content_type=content_type,
       text_content=text_content,
       external_link=external_link,
       order_index=order_index,
       is_visible=is_visible,
       is_downloadable=is_downloadable
   )
   
   file_info = None
   
   # Traiter fichier si présent
   if file and file.filename:
       # Vérifications
       if file.size > 100 * 1024 * 1024:  # 100MB max
           raise HTTPException(
               status_code=status.HTTP_400_BAD_REQUEST,
               detail="Fichier trop volumineux (max 100MB)"
           )
       
       # Types de fichiers autorisés selon le type de contenu
       allowed_types = {
           "video": ["video/mp4", "video/avi", "video/mov", "video/wmv"],
           "audio": ["audio/mp3", "audio/wav", "audio/aac", "audio/ogg"],
           "document": ["application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
           "interactive": ["application/zip", "text/html"]
       }
       
       content_type_mime = get_content_type(file.filename)

           # Ajouter la gestion pour les images
       if content_type == "image":
            if not file:
                raise HTTPException(
                    status_code=400,
                    detail="Un fichier image est requis pour ce type de contenu"
                )
            
            # Vérifier que c'est bien une image
            if not file.content_type.startswith('image/'):
                raise HTTPException(
                    status_code=400,
                    detail="Le fichier doit être une image valide"
                )
            
            # Limite de taille pour les images (10MB)
            max_size = 10 * 1024 * 1024
            if len(await file.read()) > max_size:
                raise HTTPException(
                    status_code=400,
                    detail="L'image est trop volumineuse (max 10MB)"
                )
            
            # Reset le curseur du fichier
            await file.seek(0)
       
       if content_type in allowed_types and content_type_mime not in allowed_types[content_type]:
           raise HTTPException(
               status_code=status.HTTP_400_BAD_REQUEST,
               detail=f"Type de fichier non autorisé pour {content_type}"
           )
       
       try:
           # Upload vers Supabase
           file_content = await file.read()
           
           upload_result = storage.upload_file(
               bucket_name="resources",
               file_content=file_content,
               file_name=file.filename,
               content_type=content_type_mime,
               folder=f"modules/{module_id}/contents"
           )
           
           if upload_result['success']:
               file_info = {
                   "file_url": upload_result['url'],
                   "file_path": upload_result['path'],
                   "file_size": file.size,
                   "file_type": content_type_mime,
                   "duration_seconds": None  # TODO: Extraire durée pour vidéos/audio
               }
           else:
               raise HTTPException(
                   status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                   detail=f"Erreur upload: {upload_result['error']}"
               )
               
       except Exception as e:
           raise HTTPException(
               status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
               detail=f"Erreur traitement fichier: {str(e)}"
           )
   
   # Créer contenu
   content = create_module_content(db, content_data, file_info)
   
   return ModuleContentResponse(
       content_id=content.content_id,
       module_id=content.module_id,
       title=content.title,
       description=content.description,
       content_type=content.content_type,
       text_content=content.text_content,
       external_link=content.external_link,
       file_url=content.file_url,
       file_path=content.file_path,
       file_size=content.file_size,
       file_type=content.file_type,
       duration_seconds=content.duration_seconds,
       order_index=content.order_index,
       is_visible=content.is_visible,
       is_downloadable=content.is_downloadable,
       created_at=content.created_at,
       updated_at=content.updated_at,
       is_media=content.is_media,
       duration_formatted=content.duration_formatted
   )

@router.get("/{module_id}/contents", response_model=List[ModuleContentResponse])
def get_module_contents_route(
   module_id: UUID,
   visible_only: bool = Query(True, description="Afficher seulement les contenus visibles"),
   current_user: User = Depends(get_current_user),
   db: Session = Depends(get_db)
):
   """📋 Contenus d'un module"""
   
   # Vérifier que le module existe
   module = get_module_by_id(db, module_id)
   if not module:
       raise HTTPException(
           status_code=status.HTTP_404_NOT_FOUND,
           detail="Module non trouvé"
       )
   
   contents = get_module_contents(db, module_id, visible_only)
   
   return [
       ModuleContentResponse(
           content_id=content.content_id,
           module_id=content.module_id,
           title=content.title,
           description=content.description,
           content_type=content.content_type,
           text_content=content.text_content,
           external_link=content.external_link,
           file_url=content.file_url,
           file_path=content.file_path,
           file_size=content.file_size,
           file_type=content.file_type,
           duration_seconds=content.duration_seconds,
           order_index=content.order_index,
           is_visible=content.is_visible,
           is_downloadable=content.is_downloadable,
           created_at=content.created_at,
           updated_at=content.updated_at,
           is_media=content.is_media,
           duration_formatted=content.duration_formatted
       ) for content in contents
   ]

@router.put("/contents/{content_id}", response_model=ModuleContentResponse)
def update_module_content_route(
   content_id: UUID,
   update_data: ModuleContentUpdate,
   current_user: User = Depends(require_expert),
   db: Session = Depends(get_db)
):
   """✏️ Modifier contenu de module"""
   
   content = update_module_content(db, content_id, update_data)
   
   if not content:
       raise HTTPException(
           status_code=status.HTTP_404_NOT_FOUND,
           detail="Contenu non trouvé"
       )
   
   return ModuleContentResponse(
       content_id=content.content_id,
       module_id=content.module_id,
       title=content.title,
       description=content.description,
       content_type=content.content_type,
       text_content=content.text_content,
       external_link=content.external_link,
       file_url=content.file_url,
       file_path=content.file_path,
       file_size=content.file_size,
       file_type=content.file_type,
       duration_seconds=content.duration_seconds,
       order_index=content.order_index,
       is_visible=content.is_visible,
       is_downloadable=content.is_downloadable,
       created_at=content.created_at,
       updated_at=content.updated_at,
       is_media=content.is_media,
       duration_formatted=content.duration_formatted
   )

@router.delete("/contents/{content_id}")
def delete_module_content_route(
   content_id: UUID,
   current_user: User = Depends(require_expert),
   db: Session = Depends(get_db)
):
   """🗑️ Supprimer contenu"""
   
   success = delete_module_content(db, content_id)
   
   if not success:
       raise HTTPException(
           status_code=status.HTTP_404_NOT_FOUND,
           detail="Contenu non trouvé"
       )
   
   return {"message": "Contenu supprimé avec succès"}

@router.put("/{module_id}/contents/reorder")
def reorder_contents(
   module_id: UUID,
   content_orders: List[dict],  # [{"content_id": "...", "order_index": 1}]
   current_user: User = Depends(require_expert),
   db: Session = Depends(get_db)
):
   """🔄 Réorganiser l'ordre des contenus"""
   
   success = reorder_module_contents(db, module_id, content_orders)
   
   if not success:
       raise HTTPException(
           status_code=status.HTTP_400_BAD_REQUEST,
           detail="Erreur lors de la réorganisation"
       )
   
   return {"message": "Ordre des contenus mis à jour"}

# ========== ROUTES PROGRESSION ==========

@router.post("/{module_id}/progress/start")
def start_module(
   module_id: UUID,
   current_user: User = Depends(get_current_user),
   db: Session = Depends(get_db)
):
   """🚀 Commencer un module"""
   
   if current_user.user_type.value != "entrepreneur":
       raise HTTPException(
           status_code=status.HTTP_403_FORBIDDEN,
           detail="Seuls les entrepreneurs peuvent suivre des modules"
       )
   
   entrepreneur = get_entrepreneur_by_user_id(db, current_user.user_id)
   if not entrepreneur:
       raise HTTPException(
           status_code=status.HTTP_404_NOT_FOUND,
           detail="Profil entrepreneur non trouvé"
       )
   
   progress = update_module_progress(db, module_id, entrepreneur.entrepreneur_id)
   
   return {"message": "Module commencé", "progress_id": str(progress.progress_id)}

@router.post("/{module_id}/progress/content/{content_id}")
def mark_content_as_completed(
   module_id: UUID,
   content_id: UUID,
   time_spent: Optional[int] = Query(None, description="Temps passé en minutes"),
   current_user: User = Depends(get_current_user),
   db: Session = Depends(get_db)
):
   """✅ Marquer contenu comme terminé"""
   
   if current_user.user_type.value != "entrepreneur":
       raise HTTPException(
           status_code=status.HTTP_403_FORBIDDEN,
           detail="Seuls les entrepreneurs peuvent marquer des contenus comme terminés"
       )
   
   entrepreneur = get_entrepreneur_by_user_id(db, current_user.user_id)
   if not entrepreneur:
       raise HTTPException(
           status_code=status.HTTP_404_NOT_FOUND,
           detail="Profil entrepreneur non trouvé"
       )
   
   # Mettre à jour progression générale
   progress = update_module_progress(
       db, module_id, entrepreneur.entrepreneur_id, 
       content_id, time_spent
   )
   
   # Marquer contenu spécifique comme complété
   progress = mark_content_completed(db, module_id, entrepreneur.entrepreneur_id, content_id)
   
   return {
       "message": "Contenu marqué comme terminé",
       "completion_percentage": progress.completion_percentage
   }

@router.get("/{module_id}/progress", response_model=ModuleProgressResponse)
def get_module_progress(
   module_id: UUID,
   current_user: User = Depends(get_current_user),
   db: Session = Depends(get_db)
):
   """📊 Progression dans un module"""
   
   if current_user.user_type.value != "entrepreneur":
       raise HTTPException(
           status_code=status.HTTP_403_FORBIDDEN,
           detail="Seuls les entrepreneurs ont une progression"
       )
   
   entrepreneur = get_entrepreneur_by_user_id(db, current_user.user_id)
   if not entrepreneur:
       raise HTTPException(
           status_code=status.HTTP_404_NOT_FOUND,
           detail="Profil entrepreneur non trouvé"
       )
   
   progress = get_or_create_module_progress(db, module_id, entrepreneur.entrepreneur_id)
   
   return ModuleProgressResponse(
       progress_id=progress.progress_id,
       module_id=progress.module_id,
       entrepreneur_id=progress.entrepreneur_id,
       completion_percentage=progress.completion_percentage,
       contents_completed=progress.contents_completed,
       total_contents=progress.total_contents,
       is_started=progress.is_started,
       is_completed=progress.is_completed,
       started_at=progress.started_at,
       completed_at=progress.completed_at,
       last_accessed_at=progress.last_accessed_at,
       time_spent_minutes=progress.time_spent_minutes,
       last_content_id=progress.last_content_id,
       progress_status=progress.progress_status
   )

@router.get("/my-progress", response_model=List[ModuleProgressResponse])
def get_my_module_progress(
   program_id: Optional[UUID] = Query(None, description="Filtrer par programme"),
   current_user: User = Depends(get_current_user),
   db: Session = Depends(get_db)
):
   """📈 Ma progression dans tous les modules"""
   
   if current_user.user_type.value != "entrepreneur":
       raise HTTPException(
           status_code=status.HTTP_403_FORBIDDEN,
           detail="Seuls les entrepreneurs ont une progression"
       )
   
   entrepreneur = get_entrepreneur_by_user_id(db, current_user.user_id)
   if not entrepreneur:
       raise HTTPException(
           status_code=status.HTTP_404_NOT_FOUND,
           detail="Profil entrepreneur non trouvé"
       )
   
   progress_list = get_user_module_progress(db, entrepreneur.entrepreneur_id, program_id)
   
   return [
       ModuleProgressResponse(
           progress_id=progress.progress_id,
           module_id=progress.module_id,
           entrepreneur_id=progress.entrepreneur_id,
           completion_percentage=progress.completion_percentage,
           contents_completed=progress.contents_completed,
           total_contents=progress.total_contents,
           is_started=progress.is_started,
           is_completed=progress.is_completed,
           started_at=progress.started_at,
           completed_at=progress.completed_at,
           last_accessed_at=progress.last_accessed_at,
           time_spent_minutes=progress.time_spent_minutes,
           last_content_id=progress.last_content_id,
           progress_status=progress.progress_status
       ) for progress in progress_list
   ]

# ========== RECHERCHE ET STATISTIQUES ==========

@router.get("/search", response_model=List[ModuleResponse])
def search_modules_route(
   query: str = Query(..., description="Terme de recherche"),
   module_type: Optional[str] = Query(None),
   difficulty: Optional[str] = Query(None),
   program_id: Optional[UUID] = Query(None),
   limit: int = Query(20),
   current_user: User = Depends(get_current_user),
   db: Session = Depends(get_db)
):
   """🔍 Rechercher modules"""
   
   modules = search_modules(db, query, module_type, difficulty, program_id, limit)
   
   return [
       ModuleResponse(**format_module_response(module, current_user.user_id))
       for module in modules
   ]

@router.get("/{module_id}/stats", response_model=ModuleStats)
def get_module_statistics(
   module_id: UUID,
   current_user: User = Depends(require_expert),
   db: Session = Depends(get_db)
):
   """📊 Statistiques d'un module"""
   
   stats = get_module_stats(db, module_id)
   return ModuleStats(**stats)

@router.get("/expert/my-modules", response_model=List[ModuleResponse])
def get_my_expert_modules(
   current_user: User = Depends(require_expert),
   db: Session = Depends(get_db)
):
   """📚 Mes modules créés (Expert)"""
   
   expert = get_expert_by_user_id(db, current_user.user_id)
   if not expert:
       raise HTTPException(
           status_code=status.HTTP_404_NOT_FOUND,
           detail="Profil expert non trouvé"
       )
   
   modules = get_modules_by_expert(db, expert.expert_id)
   
   return [
       ModuleResponse(**format_module_response(module, current_user.user_id))
       for module in modules
   ]