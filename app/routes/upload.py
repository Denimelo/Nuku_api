from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.dependencies import get_current_user, require_admin
from app.models.user import User
from app.schemas.upload import FileUploadResponse, FileDeleteResponse, FileListResponse
from app.utils.supabase_storage import storage, is_image, is_document, get_content_type
from typing import Optional

router = APIRouter(prefix="/upload", tags=["File Upload"])

@router.post("/profile-photo", response_model=FileUploadResponse)
async def upload_profile_photo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """📸 Upload photo de profil"""
    
    # Vérifications
    if not is_image(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seules les images sont autorisées (jpg, png, gif, webp)"
        )
    
    if file.size > 5 * 1024 * 1024:  # 5MB max
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fichier trop volumineux (max 5MB)"
        )
    
    # Upload
    file_content = await file.read()
    content_type = get_content_type(file.filename)
    
    result = storage.upload_file(
        bucket_name="profiles",
        file_content=file_content,
        file_name=file.filename,
        content_type=content_type,
        folder=f"user_{current_user.user_id}"
    )
    
    if result['success']:
        return FileUploadResponse(
            success=True,
            message="Photo de profil uploadée avec succès",
            file_url=result['url'],
            file_path=result['path'],
            bucket=result['bucket']
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur upload: {result['error']}"
        )

@router.post("/company-logo", response_model=FileUploadResponse)
async def upload_company_logo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """🏢 Upload logo d'entreprise (entrepreneurs uniquement)"""
    
    # Vérifier que c'est un entrepreneur
    if current_user.user_type.value != "entrepreneur":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les entrepreneurs peuvent uploader un logo"
        )
    
    # Vérifications fichier
    if not is_image(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seules les images sont autorisées"
        )
    
    if file.size > 2 * 1024 * 1024:  # 2MB max pour logos
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Logo trop volumineux (max 2MB)"
        )
    
    # Upload
    file_content = await file.read()
    content_type = get_content_type(file.filename)
    
    result = storage.upload_file(
        bucket_name="logos",
        file_content=file_content,
        file_name=file.filename,
        content_type=content_type,
        folder=f"company_{current_user.user_id}"
    )
    
    if result['success']:
        return FileUploadResponse(
            success=True,
            message="Logo uploadé avec succès",
            file_url=result['url'],
            file_path=result['path'],
            bucket=result['bucket']
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur upload: {result['error']}"
        )

@router.post("/document", response_model=FileUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),  # "identity_card", "registration", "professional_card", "cv"
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """📄 Upload document (entrepreneurs/experts)"""
    
    # Types de documents autorisés selon le rôle
    entrepreneur_docs = ["identity_card", "registration", "professional_card"]
    expert_docs = ["cv", "identity_card"]
    
    if current_user.user_type.value == "entrepreneur" and document_type not in entrepreneur_docs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Type de document non autorisé pour les entrepreneurs: {document_type}"
        )
    
    if current_user.user_type.value == "expert" and document_type not in expert_docs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Type de document non autorisé pour les experts: {document_type}"
        )
    
    # Vérifications fichier
    if not is_document(file.filename) and not is_image(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seuls les documents et images sont autorisés"
        )
    
    if file.size > 10 * 1024 * 1024:  # 10MB max
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fichier trop volumineux (max 10MB)"
        )
    
    # Upload
    file_content = await file.read()
    content_type = get_content_type(file.filename)
    
    result = storage.upload_file(
        bucket_name="documents",
        file_content=file_content,
        file_name=file.filename,
        content_type=content_type,
        folder=f"{current_user.user_type.value}_{current_user.user_id}/{document_type}"
    )
    
    if result['success']:
        return FileUploadResponse(
            success=True,
            message=f"Document {document_type} uploadé avec succès",
            file_url=result['url'],
            file_path=result['path'],
            bucket=result['bucket']
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur upload: {result['error']}"
        )

@router.post("/resource", response_model=FileUploadResponse)
async def upload_resource(
    file: UploadFile = File(...),
    resource_type: str = Form(...),  # "module_content", "assignment", "general"
    current_user: User = Depends(require_admin),  # Seuls les admins/experts
    db: Session = Depends(get_db)
):
    """📚 Upload ressource pédagogique (admins/experts)"""
    
    # Vérifications fichier
    if file.size > 50 * 1024 * 1024:  # 50MB max pour ressources
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fichier trop volumineux (max 50MB)"
        )
    
    # Upload
    file_content = await file.read()
    content_type = get_content_type(file.filename)
    
    result = storage.upload_file(
        bucket_name="resources",
        file_content=file_content,
        file_name=file.filename,
        content_type=content_type,
        folder=f"{resource_type}/{current_user.user_id}"
    )
    
    if result['success']:
        return FileUploadResponse(
            success=True,
            message=f"Ressource uploadée avec succès",
            file_url=result['url'],
            file_path=result['path'],
            bucket=result['bucket']
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur upload: {result['error']}"
        )

@router.delete("/file")
async def delete_file(
    bucket: str = Form(...),
    file_path: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """🗑️ Supprimer un fichier"""
    
    # Vérifier les permissions (utilisateur peut supprimer ses propres fichiers)
    if f"user_{current_user.user_id}" not in file_path and current_user.user_type.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous ne pouvez supprimer que vos propres fichiers"
        )
    
    result = storage.delete_file(bucket, file_path)
    
    if result['success']:
        return FileDeleteResponse(
            success=True,
            message="Fichier supprimé avec succès"
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur suppression: {result['error']}"
        )