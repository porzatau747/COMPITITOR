import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import httpx
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Post, Source

logger = logging.getLogger(__name__)


@dataclass
class FacebookPageConfig:
    name: str
    page_id: str
    page_url: str
    category: str | None = "Facebook Competitor"
    location: str | None = None
    priority_score: int = 80
    active: bool = True
    limit: int = 10


class FacebookGraphCollector:
    """Authorized Facebook Page collector.

    This collector intentionally uses Meta Graph API only. It does not log in with a browser,
    reuse personal accounts, bypass restrictions, or scrape protected Facebook pages.
    """

    def __init__(self, config_path: str | Path = "data/facebook_sources.json"):
        self.config_path = Path(config_path)
        self.access_token = get_settings().facebook_page_access_token

    def collect(self, db: Session, hours: int = 24) -> list[Post]:
        del hours
        if not self.access_token:
            logger.info("FACEBOOK_PAGE_ACCESS_TOKEN is not set; skipping Facebook Graph API collector")
            return []
        imported: list[Post] = []
        for source_cfg in self.load_sources():
            try:
                imported.extend(self.collect_page(db, source_cfg))
            except Exception:
                logger.exception("Facebook Graph source failed: %s", source_cfg.page_id)
        db.commit()
        return imported

    def load_sources(self) -> list[FacebookPageConfig]:
        if not self.config_path.exists():
            return []
        raw = json.loads(self.config_path.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            raw = raw.get("sources", [])
        return [FacebookPageConfig(**item) for item in raw if item.get("active", True)]

    def collect_page(self, db: Session, source_cfg: FacebookPageConfig) -> list[Post]:
        source = self._get_or_create_source(db, source_cfg)
        posts = self.fetch_posts(source_cfg)
        imported: list[Post] = []
        for item in posts:
            url = item.get("permalink_url") or f"facebook://{source_cfg.page_id}/{item.get('id')}"
            if db.query(Post).filter(Post.post_url == url).first():
                continue
            message = item.get("message") or item.get("story") or ""
            if not message.strip():
                continue
            post = Post(
                source_id=source.id,
                post_url=url,
                post_text=message[:6000],
                posted_at=_parse_facebook_datetime(item.get("created_time")),
                like_count=_summary_count(item.get("reactions")),
                comment_count=_summary_count(item.get("comments")),
                share_count=int((item.get("shares") or {}).get("count") or 0),
                view_count=0,
            )
            db.add(post)
            imported.append(post)
        db.commit()
        return imported

    def fetch_posts(self, source_cfg: FacebookPageConfig) -> list[dict]:
        fields = ",".join([
            "id",
            "message",
            "story",
            "permalink_url",
            "created_time",
            "shares",
            "comments.summary(true).limit(0)",
            "reactions.summary(true).limit(0)",
        ])
        url = f"https://graph.facebook.com/v20.0/{source_cfg.page_id}/posts"
        params = {
            "fields": fields,
            "limit": min(max(source_cfg.limit, 1), 50),
            "access_token": self.access_token,
        }
        with httpx.Client(timeout=30) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            return response.json().get("data", [])

    def _get_or_create_source(self, db: Session, source_cfg: FacebookPageConfig) -> Source:
        source = db.query(Source).filter(Source.source_url == source_cfg.page_url).first()
        if source:
            return source
        source = Source(
            name=source_cfg.name,
            platform="facebook_graph",
            source_url=source_cfg.page_url,
            source_type="facebook_page_authorized_api",
            category=source_cfg.category,
            location=source_cfg.location,
            priority_score=source_cfg.priority_score,
            active=True,
        )
        db.add(source)
        db.commit()
        db.refresh(source)
        return source


def _summary_count(value: dict | None) -> int:
    return int(((value or {}).get("summary") or {}).get("total_count") or 0)


def _parse_facebook_datetime(value: str | None):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
