from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session
from app.models import Post, Analysis, DailyReport, ContentMemory
from app.config import get_settings
from app.services.ai_analyzer_service import analyze_post
from app.services.local_adaptation_service import adapt_for_advice
from app.services.memory_service import remember_idea

def _today_in_config_timezone() -> date:
    timezone=get_settings().timezone or "Asia/Bangkok"
    return datetime.now(ZoneInfo(timezone)).date()


def _recent_ranked_posts(db: Session, limit: int = 5, days: int = 3) -> list[Post]:
    cutoff=datetime.utcnow()-timedelta(days=days)
    recent=db.query(Post).filter(Post.collected_at >= cutoff).order_by(Post.final_score.desc()).limit(limit).all()
    if len(recent) >= limit:
        return recent
    seen={p.id for p in recent}
    fallback=db.query(Post).order_by(Post.final_score.desc()).limit(limit * 2).all()
    for post in fallback:
        if post.id not in seen:
            recent.append(post); seen.add(post.id)
        if len(recent) >= limit:
            break
    return recent


def build_morning_brief(report_date: str, top_items: list[dict], market_signals: list[str], actions: dict, hooks: list[str]) -> str:
    lines=[f"📡 Advice Content Radar\nประจำวันที่ {report_date}\n", "สัญญาณตลาดวันนี้:", "เมื่อวานคอนเทนต์ไอทีที่คนสนใจมากสุดคือ:"]
    for i,s in enumerate(market_signals[:3],1): lines.append(f"{i}. {s}")
    lines.append("\n🔥 Top Content Signals")
    for item in top_items:
        lines += [f"\n{item['number']}) {item['title']}", f"แหล่งที่มา: {item['source_name']}", f"คะแนน: {item['score']}", "ทำไมถึงปัง:"]
        lines += [f"- {w}" for w in item.get('why', [])[:2]]
        lines += ["\nเอามาทำกับ Advice สามร้อยยอด:", item.get('local_adaptation','')]
        if item.get('risk'): lines += ["\nความเสี่ยง:", "- " + "\n- ".join(item['risk'])]
        lines += ["\nคำสั่งต่อยอด:", f"พิมพ์ /caption {item['number']} หรือ /carousel {item['number']} หรือ /reels {item['number']}", "---"]
    lines += ["\n🎯 คอนเทนต์ที่ควรทำวันนี้", f"A. โพสต์ขาย:\n{actions.get('sales','')}", f"B. โพสต์ความรู้:\n{actions.get('knowledge','')}", f"C. Reels/TikTok:\n{actions.get('reels','')}"]
    lines += ["\n🧲 Hook ที่น่าใช้วันนี้"] + [f"{i}. {h}" for i,h in enumerate(hooks[:5],1)]
    lines += ["\nคำสั่งที่ใช้ได้:\n /today\n /caption 1\n /carousel 1\n /reels 1\n /post_plan\n /more"]
    return "\n".join(lines)

def score_title(post: Post) -> str:
    txt=(post.post_text or "").strip()
    return txt[:55] + ("..." if len(txt)>55 else "")

def analyze_top_posts(db: Session, limit: int = 5) -> int:
    count=0
    posts=db.query(Post).order_by(Post.final_score.desc()).limit(limit * 3).all()
    for post in posts:
        if count >= limit:
            break
        if post.analysis: continue
        src_name=post.source.name if post.source else "Unknown"
        a=analyze_post(post, src_name); local=adapt_for_advice(a)
        if a.get("_analysis_mode") == "mock":
            risks=list(a.get("risk") or [])
            risks.append("AI วิเคราะห์จริงไม่สำเร็จ ระบบใช้ fallback mock analysis")
            a["risk"]=risks
        obj=Analysis(post_id=post.id, hook=a.get('hook'), hook_type=a.get('hook_type'), content_type=a.get('content_type'), pain_point=a.get('pain_point'), engagement_trigger=a.get('engagement_trigger'), why_it_worked=a.get('why_it_worked'), risk=a.get('risk'), **local)
        db.add(obj); count+=1
        remember_idea(db, local.get('caption_draft',''), local.get('suggested_hook'), post.detected_product_category, a.get('content_type'))
    db.commit(); return count

def generate_daily_report(db: Session) -> DailyReport:
    today=_today_in_config_timezone()
    posts=_recent_ranked_posts(db, limit=5, days=3)
    top=[]; hooks=[]; cats=[]
    for n,p in enumerate(posts,1):
        a=p.analysis
        src=p.source.name if p.source else "Unknown"
        why=[]
        if a and a.why_it_worked: why=[a.why_it_worked, a.pain_point or "คนมีปัญหาใกล้ตัวและอยากถามต่อ"]
        local=a.local_angle if a else "นำ pain point มาเขียนใหม่ให้เหมาะกับลูกค้าในพื้นที่"
        risk=a.risk if a else []
        hook=a.suggested_hook if a else score_title(p)
        hooks.append(hook); cats.append(p.detected_product_category or "ไอทีใกล้ตัว")
        top.append({"number":n,"post_id":p.id,"title":score_title(p),"source_name":src,"score":round(p.final_score,2),"why":why,"local_adaptation":local,"risk":risk,"hook":hook,"idea": {"local_angle": local, "suggested_hook": hook, "caption_draft": a.caption_draft if a else "", "creative_direction": a.creative_direction if a else "", "sales_bridge": a.sales_bridge if a else "", "cta": a.cta if a else ""}})
    signals=list(dict.fromkeys(cats))[:3] or ["คอมช้า/RAM/SSD", "โน้ตบุ๊กทำงาน", "Printer สำนักงาน"]
    actions={"sales":"ทำโพสต์เปิดให้ลูกค้าส่งงบ/รุ่นมาให้แอดช่วยเลือก", "knowledge":"ทำเช็กลิสต์อาการคอมช้า/เน็ตหลุด/ปริ้นเตอร์งอแง", "reels":"ถ่ายคลิป 30 วิ ก่อน-หลังแก้ปัญหาในร้าน"}
    msg=build_morning_brief(str(today), top, signals, actions, hooks)
    report=db.query(DailyReport).filter(DailyReport.report_date==today).first()
    if not report:
        report=DailyReport(report_date=today); db.add(report)
    report.summary="; ".join(signals); report.top_posts=top; report.recommended_actions=actions; report.best_hooks=hooks; report.telegram_message=msg
    db.commit(); db.refresh(report); return report

def get_idea_from_today(db: Session, number: int) -> dict | None:
    report=db.query(DailyReport).order_by(DailyReport.report_date.desc()).first()
    if not report or not report.top_posts: return None
    for item in report.top_posts:
        if item.get('number') == number: return item.get('idea') or item
    return None
