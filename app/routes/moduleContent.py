from uuid import UUID
from typing import List
from app.models.moduleContent import ModuleContent
from app.database import get_db
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from http.client import HTTPException
from app.crud.moduleContent import create_module_content, get_module_contents, get_module_content_by_id
from app.schemas.moduleContent import ModuleContentCreate, ModuleContentResponse

router = APIRouter(prefix="/module-content", tags=["ModuleContent"])

@router.post("/", response_model=ModuleContentResponse)
def create_module_content_route(data: ModuleContentCreate, db: Session = Depends(get_db)):
    return create_module_content(db, data)

@router.get("/", response_model=List[ModuleContentResponse])
def list_module_contents(db: Session = Depends(get_db)):
    return get_module_contents(db)

@router.get("/{module_content_id}", response_model=ModuleContentResponse)
def get_module_content(module_content_id: UUID, db: Session = Depends(get_db)):
    module_content = get_module_content_by_id(db, module_content_id)
    if not module_content:
        raise HTTPException(status_code=404, detail="Module content not found")
    return module_content

@router.put("/{module_content_id}", response_model=ModuleContentResponse)
def update_module_content(module_content_id: UUID, data: ModuleContentCreate, db: Session = Depends(get_db)):
    module_content = get_module_content_by_id(db, module_content_id)
    if not module_content:
        raise HTTPException(status_code=404, detail="Module content not found")
    return create_module_content(db, data, module_content_id)

@router.delete("/{module_content_id}", response_model=dict)
def delete_module_content(module_content_id: UUID, db: Session = Depends(get_db)):
    module_content = get_module_content_by_id(db, module_content_id)
    if not module_content:
        raise HTTPException(status_code=404, detail="Module content not found")
    db.delete(module_content)
    db.commit()
    return {"message": "Module content deleted successfully"}

@router.get("/module/{module_id}", response_model=List[ModuleContentResponse])
def get_module_content_by_module_id(module_id: UUID, db: Session = Depends(get_db)):
    module_contents = db.query(ModuleContent).filter(ModuleContent.module_id == module_id).all()
    if not module_contents:
        raise HTTPException(status_code=404, detail="No module contents found for this module")
    return module_contents

