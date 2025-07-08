from uuid import UUID
from typing import List
from app.database import get_db
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from http.client import HTTPException
from app.crud.call import create_call, get_calls, get_call_by_id
from app.schemas.call import CallCreate, CallResponse

router = APIRouter(prefix="/calls", tags=["Calls"])

@router.post("/", response_model=CallResponse)
def create_call_route(data: CallCreate, db: Session = Depends(get_db)):
    return create_call(db, data)

@router.get("/", response_model=List[CallResponse])
def list_calls(db: Session = Depends(get_db)):
    return get_calls(db)

@router.get("/{call_id}", response_model=CallResponse)
def get_call(call_id: UUID, db: Session = Depends(get_db)):
    call = get_call_by_id(db, call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    return call

@router.put("/{call_id}", response_model=CallResponse)
def update_call(call_id: UUID, data: CallCreate, db: Session = Depends(get_db)):
    call = get_call_by_id(db, call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    return create_call(db, data, call_id)

@router.delete("/{call_id}", response_model=dict)
def delete_call(call_id: UUID, db: Session = Depends(get_db)):
    call = get_call_by_id(db, call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    db.delete(call)
    db.commit()
    return {"message": "Call deleted successfully"}

@router.get("/program/{program_id}", response_model=List[CallResponse])
def get_calls_by_program(program_id: UUID, db: Session = Depends(get_db)):
    calls = db.query(CallResponse).filter(CallResponse.program_id == program_id).all()
    if not calls:
        raise HTTPException(status_code=404, detail="No calls found for this program")
    return calls

