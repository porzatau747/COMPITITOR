import csv, json
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from app.models import Source, Post


def _safe_int(value, default: int = 0) -> int:
    try:
        if value is None or str(value).strip() == "":
            return default
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return default


class ManualImportCollector:
    def import_file(self, db: Session, path: str) -> int:
        p=Path(path); rows=[]
        if p.suffix.lower()==".json": rows=json.loads(p.read_text(encoding="utf-8"))
        else:
            rows=list(csv.DictReader(p.open(encoding="utf-8")))
        count=0
        for row in rows:
            src=db.query(Source).filter(Source.name==row.get("source_name","Manual Import")).first()
            if not src:
                src=Source(name=row.get("source_name","Manual Import"), platform=row.get("platform","manual"), source_url=row.get("source_url","manual://import"), source_type=row.get("source_type","it_news_page"))
                db.add(src); db.commit()
            url=row.get("post_url") or f"manual://{count}-{datetime.utcnow().timestamp()}"
            if db.query(Post).filter(Post.post_url==url).first(): continue
            db.add(Post(source_id=src.id, post_url=url, post_text=row.get("post_text",""), like_count=_safe_int(row.get("like_count")), comment_count=_safe_int(row.get("comment_count")), share_count=_safe_int(row.get("share_count")), view_count=_safe_int(row.get("view_count"))))
            count+=1
        db.commit(); return count
