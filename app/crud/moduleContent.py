from sqlalchemy.orm import Session
from uuid import UUID
from app.models.moduleContent import ModuleContent
from app.schemas.moduleContent import ModuleContentCreate, ModuleContentUpdate

def create_module_content(db: Session, module_content_in: ModuleContentCreate):
    module_content = ModuleContent(**module_content_in.dict())
    db.add(module_content)
    db.commit()
    db.refresh(module_content)
    return module_content

def get_module_content(db: Session, module_content_id: UUID):
    return db.query(ModuleContent).filter(ModuleContent.module_content_id == module_content_id).first()

def get_module_contents(db: Session, skip: int = 0, limit: int = 100):
    return db.query(ModuleContent).offset(skip).limit(limit).all()

def update_module_content(db: Session, module_content_id: UUID, module_content_in: ModuleContentUpdate):
    module_content = db.query(ModuleContent).filter(ModuleContent.module_content_id == module_content_id).first()
    if not module_content:
        return None
    for field, value in module_content_in.dict(exclude_unset=True).items():
        setattr(module_content, field, value)
    db.commit()
    db.refresh(module_content)
    return module_content

def delete_module_content(db: Session, module_content_id: UUID):
    module_content = db.query(ModuleContent).filter(ModuleContent.module_content_id == module_content_id).first()
    if not module_content:
        return None
    db.delete(module_content)
    db.commit()
    return module_content

def get_module_content_by_id(db: Session, module_content_id: UUID):
    return db.query(ModuleContent).filter(ModuleContent.module_content_id == module_content_id).first()

def get_module_content_by_module_id(db: Session, module_id: UUID):
    return db.query(ModuleContent).filter(ModuleContent.module_id == module_id).all()

def get_module_content_by_program_id(db: Session, program_id: UUID):
    return db.query(ModuleContent).filter(ModuleContent.program_id == program_id).all()

def get_module_content_by_user_id(db: Session, user_id: UUID):
    return db.query(ModuleContent).filter(ModuleContent.user_id == user_id).all()