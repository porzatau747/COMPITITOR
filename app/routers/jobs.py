from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.jobs.daily_workflow import run_collect, run_score, run_analyze, run_full_daily
router=APIRouter(prefix="/jobs", tags=["jobs"])
@router.post("/collect")
def collect(db: Session=Depends(get_db)): return run_collect(db)
@router.post("/score")
def score(db: Session=Depends(get_db)): return run_score(db)
@router.post("/analyze")
def analyze(db: Session=Depends(get_db)): return run_analyze(db)
@router.post("/full-daily-run")
def full(send: bool=False, db: Session=Depends(get_db)): return run_full_daily(db, send=send)
