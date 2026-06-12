from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.ops_summary_service import build_ops_summary

router = APIRouter(prefix="/ops", tags=["ops"])


@router.get("/summary")
def ops_summary(db: Session = Depends(get_db)):
    return build_ops_summary(db)
