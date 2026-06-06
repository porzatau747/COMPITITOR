from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Source
from app.schemas.source_schema import SourceCreate, SourceOut, SourceUpdate
from app.services.source_health_service import build_source_health_report
router=APIRouter(prefix="/sources", tags=["sources"])
@router.get("/health")
def source_health(stale_hours:int=72, db: Session=Depends(get_db)):
    return build_source_health_report(db, stale_hours=stale_hours)
@router.get("", response_model=list[SourceOut])
def list_sources(limit:int=50, offset:int=0, db: Session=Depends(get_db)):
    return db.query(Source).offset(offset).limit(min(limit, 200)).all()
@router.post("", response_model=SourceOut)
def create_source(payload: SourceCreate, db: Session=Depends(get_db)):
    obj=Source(**payload.model_dump()); db.add(obj); db.commit(); db.refresh(obj); return obj
@router.put("/{source_id}", response_model=SourceOut)
def update_source(source_id:int, payload: SourceUpdate, db: Session=Depends(get_db)):
    obj=db.get(Source, source_id)
    if not obj: raise HTTPException(404,"source not found")
    for k,v in payload.model_dump().items(): setattr(obj,k,v)
    db.commit(); db.refresh(obj); return obj
@router.delete("/{source_id}")
def delete_source(source_id:int, db: Session=Depends(get_db)):
    obj=db.get(Source, source_id)
    if not obj: raise HTTPException(404,"source not found")
    db.delete(obj); db.commit(); return {"deleted": True}
