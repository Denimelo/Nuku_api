from supabase import create_client, Client
from app.config import settings
from typing import Optional, List
import os
from uuid import uuid4
from datetime import datetime

# Client Supabase
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

class SupabaseStorage:
    def __init__(self):
        self.client = supabase
    
    def upload_file(
        self, 
        bucket_name: str, 
        file_content: bytes, 
        file_name: str, 
        content_type: str = "application/octet-stream",
        folder: Optional[str] = None
    ) -> dict:
        """Upload un fichier vers Supabase Storage"""
        try:
            # Générer un nom unique pour éviter les conflits
            unique_filename = f"{uuid4()}_{file_name}"
            
            # Construire le chemin complet
            if folder:
                file_path = f"{folder}/{unique_filename}"
            else:
                file_path = unique_filename
            
            # Upload du fichier
            response = self.client.storage.from_(bucket_name).upload(
                path=file_path,
                file=file_content,
                file_options={"content-type": content_type}
            )
            
            # Vérifier le succès de l'upload
            upload_success = False
            
            if hasattr(response, 'data') and response.data is not None:
                upload_success = True
            elif hasattr(response, 'error') and response.error is None:
                upload_success = True
            elif isinstance(response, dict) and response.get('error') is None:
                upload_success = True
            else:
                # Test final : essayer de récupérer l'URL
                try:
                    test_url = self.client.storage.from_(bucket_name).get_public_url(file_path)
                    if test_url:
                        upload_success = True
                except:
                    pass
            
            if upload_success:
                # Récupérer l'URL
                if bucket_name in ['logos', 'profiles']:
                    # Bucket public - URL directe
                    file_url = self.client.storage.from_(bucket_name).get_public_url(file_path)
                else:
                    # Bucket privé - URL signée (valide 1 an)
                    signed_url_response = self.client.storage.from_(bucket_name).create_signed_url(
                        file_path, 
                        expires_in=365*24*3600  # 1 an
                    )
                    file_url = signed_url_response.get('signedURL') if signed_url_response else None
                
                return {
                    'success': True,
                    'url': file_url,
                    'path': file_path,
                    'bucket': bucket_name,
                    'error': None
                }
            else:
                error_message = "Upload failed"
                if hasattr(response, 'error') and response.error:
                    error_message = str(response.error)
                
                return {
                    'success': False,
                    'url': None,
                    'path': None,
                    'error': error_message
                }
                
        except Exception as e:
            return {
                'success': False,
                'url': None,
                'path': None,
                'error': str(e)
            }
    
    def delete_file(self, bucket_name: str, file_path: str) -> dict:
        """Supprimer un fichier"""
        try:
            response = self.client.storage.from_(bucket_name).remove([file_path])
            
            success = False
            if hasattr(response, 'data') and response.data is not None:
                success = True
            elif hasattr(response, 'error') and response.error is None:
                success = True
            
            return {
                'success': success,
                'error': None if success else f"Erreur suppression: {getattr(response, 'error', 'Unknown error')}"
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_file_url(self, bucket_name: str, file_path: str, expires_in: int = 3600) -> Optional[str]:
        """Récupérer l'URL d'un fichier"""
        try:
            if bucket_name in ['logos', 'profiles']:
                # Bucket public
                return self.client.storage.from_(bucket_name).get_public_url(file_path)
            else:
                # Bucket privé
                signed_url_response = self.client.storage.from_(bucket_name).create_signed_url(
                    file_path, 
                    expires_in=expires_in
                )
                return signed_url_response.get('signedURL') if signed_url_response else None
        except Exception as e:
            return None
    
    def list_files(self, bucket_name: str, folder: Optional[str] = None) -> List[dict]:
        """Lister les fichiers d'un bucket"""
        try:
            if folder:
                response = self.client.storage.from_(bucket_name).list(folder)
            else:
                response = self.client.storage.from_(bucket_name).list()
            
            if hasattr(response, 'data') and response.data:
                return response.data
            elif isinstance(response, list):
                return response
            else:
                return []
        except Exception as e:
            return []

# Instance globale
storage = SupabaseStorage()

# Fonctions utilitaires
def get_file_extension(filename: str) -> str:
    """Récupérer l'extension d'un fichier"""
    return os.path.splitext(filename)[1].lower()

def is_image(filename: str) -> bool:
    """Vérifier si c'est une image"""
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']
    return get_file_extension(filename) in image_extensions

def is_document(filename: str) -> bool:
    """Vérifier si c'est un document"""
    doc_extensions = ['.pdf', '.doc', '.docx', '.txt', '.rtf']
    return get_file_extension(filename) in doc_extensions

def get_content_type(filename: str) -> str:
    """Déterminer le type MIME d'un fichier"""
    ext = get_file_extension(filename)
    
    mime_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
        '.svg': 'image/svg+xml',
        '.pdf': 'application/pdf',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.txt': 'text/plain',
        '.rtf': 'application/rtf'
    }
    
    return mime_types.get(ext, 'application/octet-stream')