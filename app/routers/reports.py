from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import DailyReport
from app.schemas.report_schema import ReportOut
from app.services.report_service import generate_daily_report
from app.services.telegram_service import send_report
router=APIRouter(prefix="/reports", tags=["reports"])
@router.get("/today", response_model=ReportOut)
def today(db: Session=Depends(get_db)):
    obj=db.query(DailyReport).order_by(DailyReport.report_date.desc()).first()
    if not obj: raise HTTPException(404,"no report")
    return obj
@router.get("", response_model=list[ReportOut])
def list_reports(limit:int=30, offset:int=0, db: Session=Depends(get_db)):
    return db.query(DailyReport).order_by(DailyReport.report_date.desc()).offset(offset).limit(min(limit, 100)).all()
@router.get("/{report_id}", response_model=ReportOut)
def get_report(report_id:int, db: Session=Depends(get_db)):
    obj=db.get(DailyReport, report_id)
    if not obj: raise HTTPException(404,"report not found")
    return obj
@router.post("/generate")
def generate(db: Session=Depends(get_db)): return {"report_id": generate_daily_report(db).id}
@router.post("/send-telegram")
def send(db: Session=Depends(get_db)):
    obj=db.query(DailyReport).order_by(DailyReport.report_date.desc()).first()
    if not obj: raise HTTPException(404,"no report")
    return {"sent": send_report(db,obj)}
