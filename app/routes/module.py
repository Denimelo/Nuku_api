from uuid import UUID
from typing import List
from app.database import get_db
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from http.client import HTTPException
from app.crud.module import create_module, get_modules, get_module_by_id
from app.schemas.module import ModuleCreate, ModuleResponse

router = APIRouter(prefix="/modules", tags=["Modules"])

@router.post("/", response_model=ModuleResponse)
def create_module_route(data: ModuleCreate, db: Session = Depends(get_db)):
    return create_module(db, data)

@router.get("/", response_model=List[ModuleResponse])
def list_modules(db: Session = Depends(get_db)):
    return get_modules(db)

@router.get("/{module_id}", response_model=ModuleResponse)
def get_module(module_id: UUID, db: Session = Depends(get_db)):
    return get_module_by_id(db, module_id)

@router.put("/{module_id}", response_model=ModuleResponse)
def update_module(module_id: UUID, data: ModuleCreate, db: Session = Depends(get_db)):
    module = get_module_by_id(db, module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    return create_module(db, data, module_id)

@router.delete("/{module_id}", response_model=dict)
def delete_module(module_id: UUID, db: Session = Depends(get_db)):
    module = get_module_by_id(db, module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    db.delete(module)
    db.commit()
    return {"message": "Module deleted successfully"}


