from sqlalchemy.orm import Session
from uuid import UUID
from ..models.module import Module
from ..schemas.module import ModuleCreate, ModuleUpdate

def create_module(db: Session, module_in: ModuleCreate):
    module = Module(**module_in.dict())
    db.add(module)
    db.commit()
    db.refresh(module)
    return module

def get_module(db: Session, module_id: UUID):
    return db.query(Module).filter(Module.module_id == module_id).first()

def get_modules(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Module).offset(skip).limit(limit).all()

def update_module(db: Session, module_id: UUID, module_in: ModuleUpdate):
    module = db.query(Module).filter(Module.module_id == module_id).first()
    if not module:
        return None
    for field, value in module_in.dict(exclude_unset=True).items():
        setattr(module, field, value)
    db.commit()
    db.refresh(module)
    return module

def delete_module(db: Session, module_id: UUID):
    module = db.query(Module).filter(Module.module_id == module_id).first()
    if not module:
        return None
    db.delete(module)
    db.commit()
    return module