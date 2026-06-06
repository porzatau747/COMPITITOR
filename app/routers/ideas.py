from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import SavedIdea, DailyReport
from app.services.report_service import get_idea_from_today
router=APIRouter(prefix="/ideas", tags=["ideas"])
@router.get("/saved")
def saved(limit:int=50, offset:int=0, db: Session=Depends(get_db)):
    return db.query(SavedIdea).order_by(SavedIdea.id.desc()).offset(offset).limit(min(limit, 200)).all()
@router.post("/save")
def save(number:int=1, db: Session=Depends(get_db)):
    idea=get_idea_from_today(db, number)
    report=db.query(DailyReport).order_by(DailyReport.report_date.desc()).first()
    if not idea or not report: raise HTTPException(404,"idea not found")
    existing=db.query(SavedIdea).filter(SavedIdea.report_id==report.id, SavedIdea.idea_number==number).first()
    if existing: return existing
    obj=SavedIdea(report_id=report.id, idea_number=number, title=idea.get('suggested_hook'), local_angle=idea.get('local_angle'), suggested_hook=idea.get('suggested_hook'), caption_draft=idea.get('caption_draft'), creative_direction=idea.get('creative_direction'))
    db.add(obj); db.commit(); db.refresh(obj); return obj
@router.post("/{idea_id}/used")
def used(idea_id:int, db: Session=Depends(get_db)):
    obj=db.get(SavedIdea, idea_id)
    if not obj: raise HTTPException(404,"saved idea not found")
    obj.status='used'; obj.used_at=datetime.utcnow(); db.commit(); return {"used": True}
