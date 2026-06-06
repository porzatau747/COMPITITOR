from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Post, Source


def build_source_health_report(db: Session, stale_hours: int = 72) -> list[dict]:
    now = datetime.utcnow()
    stale_before = now - timedelta(hours=stale_hours)
    rows = []
    sources = db.query(Source).order_by(Source.priority_score.desc(), Source.name.asc()).all()
    for source in sources:
        latest_collected_at, latest_posted_at, post_count = (
            db.query(
                func.max(Post.collected_at),
                func.max(Post.posted_at),
                func.count(Post.id),
            )
            .filter(Post.source_id == source.id)
            .one()
        )
        status = "ok"
        reason = "มีข้อมูลล่าสุด"
        if not source.active:
            status = "inactive"
            reason = "source ถูกปิดใช้งาน"
        elif not post_count:
            status = "empty"
            reason = "ยังไม่เคย import โพสต์"
        elif latest_collected_at and latest_collected_at < stale_before:
            status = "stale"
            reason = f"ไม่มีข้อมูลใหม่เกิน {stale_hours} ชั่วโมง"
        rows.append({
            "source_id": source.id,
            "name": source.name,
            "platform": source.platform,
            "source_type": source.source_type,
            "source_url": source.source_url,
            "active": source.active,
            "priority_score": source.priority_score,
            "post_count": int(post_count or 0),
            "latest_collected_at": latest_collected_at.isoformat() if latest_collected_at else None,
            "latest_posted_at": latest_posted_at.isoformat() if latest_posted_at else None,
            "health_status": status,
            "reason": reason,
        })
    return rows
