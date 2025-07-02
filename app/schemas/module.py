from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional

class ModuleBase(BaseModel):
    program_id: UUID4
    title: str
    description: Optional[str] = None
    sequence_number: int

class ModuleCreate(ModuleBase):
    created_by: UUID4

class ModuleResponse(ModuleBase):
    module_id: UUID4
    created_by: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ModuleOut(ModuleBase):
    module_id: UUID4
    created_by: UUID4
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ModuleUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    sequence_number: Optional[int] = None

    class Config:
        from_attributes = True

class ModuleDelete(BaseModel):
    module_id: UUID4

    class Config:
        from_attributes = True