from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.crud.program import create_program, get_program_by_id, get_all_programs
from app.schemas.program import ProgramCreate, ProgramResponse
from typing import List
from uuid import UUID

router = APIRouter(prefix="/programs", tags=["Programs"])

@router.post("/", response_model=ProgramResponse)
def create_new_program(payload: ProgramCreate, db: Session = Depends(get_db)):
    return create_program(db, payload)

@router.get("/", response_model=List[ProgramResponse])
def list_programs(db: Session = Depends(get_db)):
    return get_all_programs(db)

@router.get("/{program_id}", response_model=ProgramResponse)
def retrieve_program(program_id: UUID, db: Session = Depends(get_db)):
    program = get_program_by_id(db, program_id)
    if not program:
        raise HTTPException(status_code=404, detail="Programme non trouvé")
    return program

@router.put("/{program_id}", response_model=ProgramResponse)
def update_program(program_id: UUID, payload: ProgramCreate, db: Session = Depends(get_db)):
    program = get_program_by_id(db, program_id)
    if not program:
        raise HTTPException(status_code=404, detail="Programme non trouvé")
    return create_program(db, payload, program_id)

@router.delete("/{program_id}", response_model=dict)
def delete_program(program_id: UUID, db: Session = Depends(get_db)):
    program = get_program_by_id(db, program_id)
    if not program:
        raise HTTPException(status_code=404, detail="Programme non trouvé")
    db.delete(program)
    db.commit()
    return {"message": "Programme supprimé avec succès"}

