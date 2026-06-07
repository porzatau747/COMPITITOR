# แผนการดำเนินงาน: ตัวดึงข้อมูล Facebook ด้วย CloakBrowser

> **สำหรับ Antigravity:** ขั้นตอนการทำงานที่ต้องปฏิบัติ: ใช้ `.agent/workflows/execute-plan.md` เพื่อรันแผนงานนี้ในแบบ single-flow mode

**เป้าหมาย:** พัฒนาตัวรวบรวมข้อมูลเพจคู่แข่ง Facebook (`FacebookCloakCollector`) ที่ทำงานผ่าน CloakBrowser เพื่อดึงโพสต์สาธารณะและยอดการมีส่วนร่วม (Engagement Metrics) มาบันทึกในฐานข้อมูล

**สถาปัตยกรรม:** อ่านเป้าหมาย URL จากไฟล์คอนฟิก JSON, เรียกใช้ CloakBrowser (Playwright) เพื่อเปิดหน้าเพจสาธารณะ, เลื่อนหน้าจอเล็กน้อยเพื่อให้ข้อมูลโหลดครบถ้วน, แกะข้อความ ลิงก์โพสต์ (Permalink) และยอดผู้ใช้มีส่วนร่วมจากโค้ด HTML แล้วเซฟลงฐานข้อมูล

**เครื่องมือที่ใช้:** Python, Playwright (CloakBrowser), lxml/BeautifulSoup, SQLite/PostgreSQL, SQLAlchemy

---

### ขั้นตอนที่ 1: สร้างไฟล์การตั้งค่า (Configuration File)

**ไฟล์ที่เกี่ยวข้อง:**
- สร้างไฟล์ใหม่: `data/facebook_cloak_sources.json`

**ขั้นย่อย 1: เขียนไฟล์คอนฟิก**

สร้างไฟล์ `data/facebook_cloak_sources.json` ด้วยเนื้อหาต่อไปนี้:

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

**ขั้นย่อย 2: รันการตรวจสอบความถูกต้อง**

รันคำสั่ง: `python -c "import json; json.load(open('data/facebook_cloak_sources.json', encoding='utf-8'))"`
ผลลัพธ์ที่คาดหวัง: รันผ่านสำเร็จ ไม่มีข้อผิดพลาดทางไวยากรณ์ JSON

**ขั้นย่อย 3: บันทึก Git Commit**

```bash
git add data/facebook_cloak_sources.json
git commit -m "feat: add facebook cloak sources config file"
```

---

### ขั้นตอนที่ 2: เขียนชุดทดสอบของตัวสะสมข้อมูล (Collector Tests)

**ไฟล์ที่เกี่ยวข้อง:**
- สร้างไฟล์ใหม่: `tests/test_facebook_cloak_collector.py`

**ขั้นย่อย 1: เขียนชุดทดสอบที่คาดว่าจะล้มเหลว (Failing Test)**

เขียนไฟล์สำหรับทดสอบตรรกะการแกะข้อมูล (Parsing Logic)

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

**ขั้นย่อย 2: รันชุดทดสอบเพื่อยืนยันว่าทำงานล้มเหลว**

รันคำสั่ง: `python -m pytest tests/test_facebook_cloak_collector.py -v`
ผลลัพธ์ที่คาดหวัง: เกิดข้อผิดพลาด (FAIL) เนื่องจากยังไม่มีคลาสหรือโมดูล `FacebookCloakCollector` ในระบบ

**ขั้นย่อย 3: บันทึก Git Commit**

```bash
git add tests/test_facebook_cloak_collector.py
git commit -m "test: add tests for facebook cloak collector parsing logic"
```

---

### ขั้นตอนที่ 3: พัฒนาคลาส FacebookCloakCollector

**ไฟล์ที่เกี่ยวข้อง:**
- สร้างไฟล์ใหม่: `app/collectors/facebook_cloak_collector.py`

**ขั้นย่อย 1: พัฒนาฟังก์ชันการทำงาน**

สร้างไฟล์ `app/collectors/facebook_cloak_collector.py` พร้อมเขียนฟังก์ชันแปลงยอด Engagement และการดึงข้อมูลผ่านหน้าเว็บบน CloakBrowser:

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

**ขั้นย่อย 2: รันชุดทดสอบเพื่อยืนยันว่าทำงานผ่าน**

รันคำสั่ง: `python -m pytest tests/test_facebook_cloak_collector.py -v`
ผลลัพธ์ที่คาดหวัง: ผ่านการทดสอบทั้งหมด (PASS)

**ขั้นย่อย 3: บันทึก Git Commit**

```bash
git add app/collectors/facebook_cloak_collector.py
git commit -m "feat: implement FacebookCloakCollector class"
```

---

### ขั้นตอนที่ 4: เชื่อมต่อระบบเข้ากับ Collector Service หลัก

**ไฟล์ที่เกี่ยวข้อง:**
- แก้ไขไฟล์เดิม: `app/services/collector_service.py`

**ขั้นย่อย 1: ปรับปรุงโค้ดเชื่อมต่อ**

แก้ไขไฟล์ `app/services/collector_service.py` เพื่อเรียกใช้งานโมดูลใหม่ในการรันงานปกติ (ไม่ใช่ Mock Mode):

```diff
@@ -3,6 +3,7 @@
 from app.config import get_settings
 from app.collectors.mock_collector import MockCollector
 from app.collectors.web_agent_collector import WebAgentCollector
 from app.collectors.facebook_graph_collector import FacebookGraphCollector
+from app.collectors.facebook_cloak_collector import FacebookCloakCollector
 logger=logging.getLogger(__name__)
 
 def collect_recent_posts(db: Session, hours: int = 24) -> int:
@@ -14,6 +15,7 @@
         else:
             posts=[]
             posts.extend(WebAgentCollector().collect(db, hours=hours))
             posts.extend(FacebookGraphCollector().collect(db, hours=hours))
+            posts.extend(FacebookCloakCollector().collect(db, hours=hours))
             if not posts:
```

**ขั้นย่อย 2: รันการตรวจสอบความถูกต้องทั้งหมด**

รันคำสั่ง: `python -m pytest tests/`
ผลลัพธ์ที่คาดหวัง: ผ่านการทดสอบทั้งหมด 100% (รวม 21 เคสและไม่มีการทำงานที่สะดุด)

**ขั้นย่อย 3: บันทึก Git Commit**

```bash
git add app/services/collector_service.py
git commit -m "feat: integrate FacebookCloakCollector into collector service"
```
