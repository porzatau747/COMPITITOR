# Facebook Cloak Scraper Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Implement a dedicated Facebook competitor page collector (`FacebookCloakCollector`) that runs via CloakBrowser to fetch public posts and their engagement metrics.

**Architecture:** Reads target URLs from a JSON file, uses CloakBrowser (playwright) to load page feeds, scrolls page to fetch posts, extracts text, permalinks and counts from HTML, and saves to database.

**Tech Stack:** Python, Playwright (CloakBrowser), lxml/BeautifulSoup, SQLite/PostgreSQL, SQLAlchemy.

---

### Task 1: Create Configuration File

**Files:**
- Create: `data/facebook_cloak_sources.json`

**Step 1: Write the config file**

Create `data/facebook_cloak_sources.json` with the following content:

```json
{
  "sources": [
    {
      "name": "Advice Prachuap Khiri Khan",
      "url": "https://www.facebook.com/AdvicePrachuapKhiriKhan",
      "platform": "facebook_cloak",
      "source_type": "facebook_page_public",
      "category": "IT Retail",
      "location": "Prachuap Khiri Khan",
      "priority_score": 85,
      "limit_posts": 5,
      "active": true
    },
    {
      "name": "Advice Phichit",
      "url": "https://www.facebook.com/AdvicePhichit",
      "platform": "facebook_cloak",
      "source_type": "facebook_page_public",
      "category": "IT Retail",
      "location": "Phichit",
      "priority_score": 85,
      "limit_posts": 5,
      "active": true
    },
    {
      "name": "comcraft.ds",
      "url": "https://www.facebook.com/comcraft.ds",
      "platform": "facebook_cloak",
      "source_type": "facebook_page_public",
      "category": "IT Tips",
      "location": null,
      "priority_score": 80,
      "limit_posts": 5,
      "active": true
    },
    {
      "name": "notebookspec",
      "url": "https://www.facebook.com/notebookspec",
      "platform": "facebook_cloak",
      "source_type": "facebook_page_public",
      "category": "Hardware News",
      "location": null,
      "priority_score": 80,
      "limit_posts": 5,
      "active": true
    },
    {
      "name": "overclockzonefanpage",
      "url": "https://www.facebook.com/overclockzonefanpage",
      "platform": "facebook_cloak",
      "source_type": "facebook_page_public",
      "category": "Hardware News",
      "location": null,
      "priority_score": 80,
      "limit_posts": 5,
      "active": true
    },
    {
      "name": "techhub.arip",
      "url": "https://www.facebook.com/techhub.arip",
      "platform": "facebook_cloak",
      "source_type": "facebook_page_public",
      "category": "IT News",
      "location": null,
      "priority_score": 80,
      "limit_posts": 5,
      "active": true
    },
    {
      "name": "CPUCore2Duo",
      "url": "https://www.facebook.com/CPUCore2Duo",
      "platform": "facebook_cloak",
      "source_type": "facebook_page_public",
      "category": "IT Tips",
      "location": null,
      "priority_score": 80,
      "limit_posts": 5,
      "active": true
    },
    {
      "name": "itcityofficial",
      "url": "https://www.facebook.com/itcityofficial",
      "platform": "facebook_cloak",
      "source_type": "facebook_page_public",
      "category": "IT Retail",
      "location": null,
      "priority_score": 80,
      "limit_posts": 5,
      "active": true
    }
  ]
}
```

**Step 2: Run verification**

Run: `python -c "import json; json.load(open('data/facebook_cloak_sources.json', encoding='utf-8'))"`
Expected: Complete successfully (no json parse error)

**Step 3: Commit**

```bash
git add data/facebook_cloak_sources.json
git commit -m "feat: add facebook cloak sources config file"
```

---

### Task 2: Create Collector Tests

**Files:**
- Create: `tests/test_facebook_cloak_collector.py`

**Step 1: Write failing test**

Write unit tests that mock HTML parsing.

```python
from app.collectors.facebook_cloak_collector import parse_facebook_post, parse_engagement_number

def test_parse_engagement_number():
    assert parse_engagement_number("12") == 12
    assert parse_engagement_number("1.2K") == 1200
    assert parse_engagement_number("3.5M") == 3500000
    assert parse_engagement_number("0") == 0
    assert parse_engagement_number(None) == 0

def test_parse_facebook_post_html():
    html_fragment = """
    <div role="article">
      <div data-ad-preview="message">โน้ตบุ๊กทำงานแรงสุดขีด RAM 32GB ราคาประหยัด</div>
      <a href="https://www.facebook.com/permalink.php?story_fbid=123&id=456">2 hrs</a>
      <div>
        <span>ถูกใจ 1.5K คน</span>
        <span>ความคิดเห็น 120 รายการ</span>
        <span>แชร์ 45 ครั้ง</span>
      </div>
    </div>
    """
    post = parse_facebook_post(html_fragment, "https://www.facebook.com")
    assert post is not None
    assert "โน้ตบุ๊กทำงานแรงสุดขีด" in post["text"]
    assert post["url"] == "https://www.facebook.com/permalink.php?story_fbid=123&id=456"
    assert post["likes"] == 1500
    assert post["comments"] == 120
    assert post["shares"] == 45
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_facebook_cloak_collector.py -v`
Expected: FAIL due to missing imports or missing module.

**Step 3: Commit**

```bash
git add tests/test_facebook_cloak_collector.py
git commit -m "test: add tests for facebook cloak collector parsing logic"
```

---

### Task 3: Implement FacebookCloakCollector

**Files:**
- Create: `app/collectors/facebook_cloak_collector.py`

**Step 1: Write implementation**

Create `app/collectors/facebook_cloak_collector.py` with parsing utility functions and the collector class:

```python
import json
import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
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
            return []
        raw = json.loads(self.config_path.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            raw = raw.get("sources", [])
        return [
            FacebookCloakConfig(**item) for item in raw if item.get("active", True)
        ]

    def collect(self, db: Session, hours: int = 24) -> list[Post]:
        sources = self.load_sources()
        imported = []
        for src_cfg in sources:
            try:
                imported.extend(self.collect_source(db, src_cfg))
            except Exception:
                logger.exception("Facebook cloak source failed: %s", src_cfg.url)
        db.commit()
        return imported

    def collect_source(self, db: Session, src_cfg: FacebookCloakConfig) -> list[Post]:
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
                
            # Check if post url exists
            if db.query(Post).filter(Post.post_url == post_data["url"]).first():
                continue
                
            post = Post(
                source_id=source.id,
                post_url=post_data["url"],
                post_text=post_data["text"][:6000],
                media_url=None,
                posted_at=datetime.utcnow(), # Default to now for public posts
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
        from cloakbrowser import launch
        browser = launch(headless=True)
        try:
            page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            page.goto(url, wait_until="networkidle", timeout=30000)
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
```

**Step 2: Run verification**

Run: `python -m pytest tests/test_facebook_cloak_collector.py -v`
Expected: PASS

**Step 3: Commit**

```bash
git add app/collectors/facebook_cloak_collector.py
git commit -m "feat: implement FacebookCloakCollector class"
```

---

### Task 4: Integrate into Collector Service

**Files:**
- Modify: `app/services/collector_service.py`

**Step 1: Write implementation**

Modify `app/services/collector_service.py` to import and call the new collector:

```diff
-from app.collectors.facebook_graph_collector import FacebookGraphCollector
+from app.collectors.facebook_graph_collector import FacebookGraphCollector
+from app.collectors.facebook_cloak_collector import FacebookCloakCollector

 def collect_recent_posts(db: Session, hours: int = 24) -> int:
         if settings.mock_mode:
             posts=MockCollector().collect(db, hours=hours)
         else:
             posts=[]
             posts.extend(WebAgentCollector().collect(db, hours=hours))
             posts.extend(FacebookGraphCollector().collect(db, hours=hours))
+            posts.extend(FacebookCloakCollector().collect(db, hours=hours))
             if not posts:
```

**Step 2: Run verification**

Run: `python -m pytest tests/`
Expected: 100% tests pass (no errors, no syntax regressions)

**Step 3: Commit**

```bash
git add app/services/collector_service.py
git commit -m "feat: integrate FacebookCloakCollector into collector service"
```
