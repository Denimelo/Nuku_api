from pydantic import BaseModel, UUID4
from datetime import datetime

class ProgramExpertBase(BaseModel):
    program_id: UUID4
    expert_id: UUID4
    role: str

class ProgramExpertCreate(ProgramExpertBase):
    assigned_by: UUID4

class ProgramExpertResponse(ProgramExpertBase):
    program_expert_id: UUID4
    assigned_by: UUID4
    assigned_at: datetime

    class Config:
        from_attributes = True

class ProgramExpertOut(ProgramExpertBase):
    program_expert_id: UUID4
    assigned_by: UUID4
    assigned_at: datetime

    class Config:
        from_attributes = True

class ProgramExpertUpdate(BaseModel):
    role: str

    class Config:
        from_attributes = True

class ProgramExpertDelete(BaseModel):
    program_expert_id: UUID4

    class Config:
        from_attributes = True