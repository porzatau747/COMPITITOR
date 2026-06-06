from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models import ContentMemory

def recent_idea_texts(db: Session, days: int = 14) -> list[str]:
    cutoff=datetime.utcnow()-timedelta(days=days)
    return [m.idea_text or "" for m in db.query(ContentMemory).filter(ContentMemory.created_at>=cutoff).all()]

def remember_idea(db: Session, idea_text: str, hook: str | None, product_category: str | None, content_type: str | None):
    obj=ContentMemory(idea_text=idea_text, hook=hook, product_category=product_category, content_type=content_type)
    db.add(obj); db.commit(); return obj
