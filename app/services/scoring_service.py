from datetime import datetime, timezone

HIGH_KEYWORDS = {
    "Notebook": ["notebook", "โน้ตบุ๊ก", "โน๊ตบุ๊ค", "laptop"],
    "PC": ["pc", "คอม", "computer"],
    "Printer": ["printer", "ปริ้น", "ปริ้นเตอร์", "หมึก"],
    "Monitor": ["monitor", "จอ", "จอมอนิเตอร์"],
    "Router": ["router", "wifi", "ไวไฟ", "เน็ต"],
    "CCTV": ["cctv", "กล้องวงจรปิด"],
    "Keyboard": ["keyboard", "คีย์บอร์ด"],
    "Mouse": ["mouse", "เมาส์"],
    "Gaming Gear": ["gaming", "เกมมิ่ง", "หูฟัง"],
    "SSD": ["ssd"],
    "RAM": ["ram", "แรม"],
    "UPS": ["ups", "สำรองไฟ"],
    "Office Equipment": ["สำนักงาน", "office", "ออฟฟิศ"],
    "Repair Service": ["ซ่อม", "ล้างเครื่อง", "ลงวินโดว์", "คอมช้า"]
}
LOW_KEYWORDS = ["มือถือ", "smartphone", "เคสโทรศัพท์", "ดราม่า", "meme", "มีม", "ข่าวไกลตัว"]

def calculate_raw_viral_score(like_count=0, comment_count=0, share_count=0, view_count=0) -> float:
    return (like_count or 0) * 1 + (comment_count or 0) * 3 + (share_count or 0) * 5 + (view_count or 0) * 0.1


def average_raw_score(posts) -> float | None:
    scores = [calculate_raw_viral_score(p.like_count, p.comment_count, p.share_count, p.view_count) for p in posts]
    scores = [s for s in scores if s > 0]
    if not scores:
        return None
    return sum(scores) / len(scores)

def detect_categories(text: str | None) -> list[str]:
    t=(text or "").lower()
    return [cat for cat,kws in HIGH_KEYWORDS.items() if any(k.lower() in t for k in kws)]

def local_relevance_score(text: str | None) -> float:
    t=(text or "").lower()
    penalty=35 if any(k in t for k in LOW_KEYWORDS) else 0
    cats=detect_categories(t)
    if not cats: return max(10, 35-penalty)
    return min(100, 45 + len(cats)*14 - penalty)

def freshness_score(posted_at=None) -> float:
    if not posted_at: return 80
    now=datetime.now(timezone.utc).replace(tzinfo=None)
    hours=max(0, (now-posted_at).total_seconds()/3600)
    return max(0, 100 - hours*3)

def novelty_score(text: str | None, recent_ideas: list[str] | None = None) -> float:
    if not recent_ideas: return 100
    words=set((text or "").lower().split())
    if not words: return 80
    max_overlap=0
    for idea in recent_ideas:
        iw=set((idea or "").lower().split())
        if iw: max_overlap=max(max_overlap, len(words & iw)/len(words | iw))
    return max(0, 100 - max_overlap*100)

def final_score(normalized_score: float, local_relevance: float, freshness: float, novelty: float) -> float:
    # Keep the required weights, but cap the engagement component to 0–100
    # so a huge meme/mobile post cannot beat locally sellable IT ideas by raw volume alone.
    engagement = max(0, min(100, normalized_score))
    return round((engagement*0.4) + (local_relevance*0.4) + (freshness*0.1) + (novelty*0.1), 2)

def score_post(post, average_raw: float | None = None, recent_ideas: list[str] | None = None):
    raw=calculate_raw_viral_score(post.like_count, post.comment_count, post.share_count, post.view_count)
    normalized=raw / average_raw if average_raw and average_raw > 0 else raw
    local=local_relevance_score(post.post_text)
    fresh=freshness_score(post.posted_at)
    novel=novelty_score(post.post_text, recent_ideas)
    post.raw_viral_score=raw
    post.normalized_score=normalized
    post.local_relevance_score=local
    post.final_score=final_score(normalized, local, fresh, novel)
    cats=detect_categories(post.post_text)
    post.detected_product_category=", ".join(cats) if cats else None
    return post
