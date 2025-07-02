import os
import shutil
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import UserType
from app.crud.entrepreneur import get_entrepreneur_by_user_id
from app.auth.dependencies import get_current_user
from app.schemas.entrepreneur import EntrepreneurResponse

router = APIRouter(prefix="/entrepreneurs", tags=["entrepreneurs"])

# 🔍 Obtenir le profil entrepreneur de l'utilisateur connecté
@router.get("/me", response_model=EntrepreneurResponse)
def get_my_entrepreneur_profile(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if current_user.user_type != UserType.entrepreneur:
        raise HTTPException(status_code=403, detail="Accès réservé aux entrepreneurs")

    entrepreneur = get_entrepreneur_by_user_id(db, current_user.user_id)
    if not entrepreneur:
        raise HTTPException(status_code=404, detail="Profil entrepreneur non trouvé")

    return entrepreneur


@router.post("/upload-documents")
def upload_documents(
    identity_card: UploadFile = File(...),
    company_logo: UploadFile = File(...),
    registration_doc: UploadFile = File(...),
    professional_card: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    upload_dir = "uploads/entrepreneurs"
    os.makedirs(upload_dir, exist_ok=True)

    # Génère les chemins de stockage
    files = {
        "identity_card": identity_card,
        "company_logo": company_logo,
        "registration_doc": registration_doc,
        "professional_card": professional_card,
    }

    saved_paths = {}

    for key, file in files.items():
        path = os.path.join(upload_dir, f"{current_user.user_id}_{key}_{file.filename}")
        with open(path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        saved_paths[key] = path

    # Mets à jour l'entrepreneur en base de données avec les paths
    from app.models.entrepreneur import Entrepreneur
    entrepreneur = db.query(Entrepreneur).filter_by(user_id=current_user.user_id).first()
    entrepreneur.identity_card_url = saved_paths["identity_card"]
    entrepreneur.company_logo_url = saved_paths["company_logo"]
    entrepreneur.registration_doc_url = saved_paths["registration_doc"]
    entrepreneur.professional_card_url = saved_paths["professional_card"]
    db.commit()

    return {"message": "Fichiers enregistrés avec succès"}
