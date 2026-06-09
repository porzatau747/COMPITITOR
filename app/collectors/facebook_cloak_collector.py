import json
import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from lxml import html
from sqlalchemy.orm import Session
from app.config import get_settings
from app.models import Post, Source

logger = logging.getLogger(__name__)

@dataclass
class FacebookCloakConfig:
    name: str
    url: str
    platform: str = "facebook_cloak"
    source_type: str = "facebook_page_public"
    category: str | None = None
    location: str | None = None
    priority_score: int = 80
    limit_posts: int = 5
    active: bool = True

def parse_engagement_number(text: str | None) -> int:
    if not text:
        return 0
    cleaned = text.strip().replace(",", "")
    match = re.search(r"(\d+(\.\d+)?)\s*([KkMm]?)", cleaned)
    if not match:
        return 0
    val = float(match.group(1))
    suffix = match.group(3).upper()
    if suffix == "K":
        val *= 1000
    elif suffix == "M":
        val *= 1000000
    return int(val)

def parse_facebook_post(html_str: str, base_url: str) -> dict | None:
    doc = html.fromstring(html_str)
    
    # Try to find message text
    text_nodes = doc.xpath("//div[@data-ad-preview='message']//text() | //div[@dir='auto']//text()")
    if text_nodes:
        post_text = " ".join([t.strip() for t in text_nodes if t.strip()])
    else:
        # Fallback to all texts inside article, filter out UI actions
        all_texts = doc.xpath(".//text()")
        post_text = " ".join([t.strip() for t in all_texts if len(t.strip()) > 3])
    
    if not post_text or len(post_text) < 15:
        return None

    # Try to find post permalink
    anchors = doc.xpath(".//a[@href]")
    post_url = None
    for a in anchors:
        href = a.get("href") or ""
        if any(token in href for token in ["/posts/", "/permalink.php", "/photos/", "/videos/", "story_fbid="]):
            if href.startswith("/"):
                post_url = "https://www.facebook.com" + href
            else:
                post_url = href
            # Clean up query params if not permalink.php
            if "permalink.php" not in post_url and "?" in post_url:
                post_url = post_url.split("?")[0]
            break
            
    if not post_url:
        return None

    # Parse Likes, Comments, Shares
    likes = 0
    comments = 0
    shares = 0
    
    text_content = " ".join(doc.xpath(".//text()")).lower()
    
    # Simple regex search inside text content of post
    like_match = re.search(r"ถูกใจ\s*(\d+(\.\d+)?[KkMm]?)|(\d+(\.\d+)?[KkMm]?)\s*likes?", text_content)
    if like_match:
        likes = parse_engagement_number(like_match.group(1) or like_match.group(3))
        
    comment_match = re.search(r"ความคิดเห็น\s*(\d+(\.\d+)?[KkMm]?)|(\d+(\.\d+)?[KkMm]?)\s*comments?", text_content)
    if comment_match:
        comments = parse_engagement_number(comment_match.group(1) or comment_match.group(3))
        
    share_match = re.search(r"แชร์\s*(\d+(\.\d+)?[KkMm]?)|(\d+(\.\d+)?[KkMm]?)\s*shares?", text_content)
    if share_match:
        shares = parse_engagement_number(share_match.group(1) or share_match.group(3))

    return {
        "text": post_text,
        "url": post_url,
        "likes": likes,
        "comments": comments,
        "shares": shares
    }

class FacebookCloakCollector:
    def __init__(self, config_path: str | Path = "data/facebook_cloak_sources.json"):
        self.config_path = Path(config_path)

    def load_sources(self) -> list[FacebookCloakConfig]:
        if not self.config_path.exists():
            raw = []
        else:
            raw = json.loads(self.config_path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                raw = raw.get("sources", [])
        
        configs = [
            FacebookCloakConfig(**item) for item in raw if item.get("active", True)
        ]
        
        forced_urls = [
            "https://www.facebook.com/AdvicePrachuapKhiriKhan",
            "https://www.facebook.com/AdvicePhichit",
            "https://www.facebook.com/comcraft.ds",
            "https://www.facebook.com/notebookspec",
            "https://www.facebook.com/overclockzonefanpage",
            "https://www.facebook.com/techhub.arip",
            "https://www.facebook.com/CPUCore2Duo",
            "https://www.facebook.com/itcityofficial"
        ]
        
        filtered_configs = []
        for url in forced_urls:
            found = False
            for cfg in configs:
                if cfg.url.lower().rstrip('/') == url.lower().rstrip('/'):
                    filtered_configs.append(cfg)
                    found = True
                    break
            if not found:
                name = url.rstrip('/').split('/')[-1]
                default_cfg = FacebookCloakConfig(
                    name=name,
                    url=url,
                    platform="facebook_cloak",
                    source_type="facebook_page_public",
                    priority_score=80,
                    limit_posts=5,
                    active=True
                )
                filtered_configs.append(default_cfg)
                
        return filtered_configs

    def collect(self, db: Session, hours: int = 24) -> list[Post]:
        sources = self.load_sources()
        imported = []
        seen_urls = set()
        for src_cfg in sources:
            try:
                imported.extend(self.collect_source(db, src_cfg, seen_urls))
            except Exception:
                logger.exception("Facebook cloak source failed: %s", src_cfg.url)
        db.commit()
        return imported

    def collect_source(self, db: Session, src_cfg: FacebookCloakConfig, seen_urls: set[str]) -> list[Post]:
        source = self._get_or_create_source(db, src_cfg)
        html_text = self.fetch_page(src_cfg.url)
        if not html_text:
            logger.warning("No content fetched for %s", src_cfg.url)
            return []
            
        doc = html.fromstring(html_text)
        articles = doc.xpath("//div[@role='article']")
        
        imported = []
        count = 0
        for art in articles:
            if count >= src_cfg.limit_posts:
                break
            art_html = html.tostring(art, encoding="utf-8").decode("utf-8")
            post_data = parse_facebook_post(art_html, "https://www.facebook.com")
            if not post_data:
                continue
                
            url = post_data["url"]
            if url in seen_urls:
                continue
            # Check if post url exists in database
            if db.query(Post).filter(Post.post_url == url).first():
                seen_urls.add(url)
                continue
                
            seen_urls.add(url)
            post = Post(
                source_id=source.id,
                post_url=url,
                post_text=post_data["text"][:6000],
                media_url=None,
                posted_at=datetime.now(timezone.utc).replace(tzinfo=None), # Default to now for public posts
                like_count=post_data["likes"],
                comment_count=post_data["comments"],
                share_count=post_data["shares"],
                view_count=0
            )
            db.add(post)
            imported.append(post)
            count += 1
            
        return imported

    def fetch_page(self, url: str) -> str | None:
        parsed = urlparse(url)
        if parsed.netloc.lower() not in {"www.facebook.com", "facebook.com"}:
            raise ValueError(f"Invalid Facebook domain: {url}")
        from cloakbrowser import launch
        browser = launch(
            headless=True,
            stealth_args=True,
            geoip=True,
            humanize=True
        )
        try:
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            settings = get_settings()
            if settings.facebook_cookie_c_user and settings.facebook_cookie_xs:
                context.add_cookies([
                    {
                        "name": "c_user",
                        "value": settings.facebook_cookie_c_user.strip(),
                        "domain": ".facebook.com",
                        "path": "/",
                    },
                    {
                        "name": "xs",
                        "value": settings.facebook_cookie_xs.strip(),
                        "domain": ".facebook.com",
                        "path": "/",
                    }
                ])
                logger.info("Applied Facebook login cookies (c_user and xs) to Playwright context")
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            # Scroll down to load posts and bypass popup
            page.evaluate("window.scrollBy(0, 1200)")
            time.sleep(3)
            return page.content()
        finally:
            browser.close()

    def _get_or_create_source(self, db: Session, cfg: FacebookCloakConfig) -> Source:
        source = db.query(Source).filter(Source.source_url == cfg.url).first()
        if source:
            return source
        source = Source(
            name=cfg.name,
            platform=cfg.platform,
            source_url=cfg.url,
            source_type=cfg.source_type,
            category=cfg.category,
            location=cfg.location,
            priority_score=cfg.priority_score
        )
        db.add(source)
        db.commit()
        db.refresh(source)
        return source
