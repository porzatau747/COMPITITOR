import logging, httpx
from datetime import datetime
from sqlalchemy.orm import Session
from app.config import get_settings
from app.models import DailyReport, SavedIdea
from app.services.agent_os_service import is_agent_os_command, render_agent_os_command
from app.services.report_service import get_idea_from_today
from app.services.telegram_command_service import parse_number_arg, render_caption_response, render_carousel_response, render_reels_response
logger=logging.getLogger(__name__)
TELEGRAM_MESSAGE_LIMIT = 4096


def split_telegram_message(text: str, limit: int = TELEGRAM_MESSAGE_LIMIT) -> list[str]:
    if len(text or "") <= limit:
        return [text or ""]
    chunks=[]
    remaining=text or ""
    while remaining:
        chunk=remaining[:limit]
        split_at=max(chunk.rfind("\n"), chunk.rfind(" "))
        if split_at <= 0 or len(remaining) <= limit:
            split_at=limit
        chunks.append(remaining[:split_at])
        remaining=remaining[split_at:]
    return chunks

def save_idea_number(db: Session, number: int) -> SavedIdea | None:
    idea=get_idea_from_today(db, number)
    report=db.query(DailyReport).order_by(DailyReport.report_date.desc()).first()
    if not idea or not report: return None
    existing=db.query(SavedIdea).filter(SavedIdea.report_id==report.id, SavedIdea.idea_number==number).first()
    if existing: return existing
    obj=SavedIdea(report_id=report.id, idea_number=number, title=idea.get('suggested_hook'), local_angle=idea.get('local_angle'), suggested_hook=idea.get('suggested_hook'), caption_draft=idea.get('caption_draft'), creative_direction=idea.get('creative_direction'))
    db.add(obj); db.commit(); db.refresh(obj); return obj

def mark_idea_used(db: Session, number: int) -> SavedIdea | None:
    report=db.query(DailyReport).order_by(DailyReport.report_date.desc()).first()
    if not report: return None
    obj=db.query(SavedIdea).filter(SavedIdea.report_id==report.id, SavedIdea.idea_number==number).first() or save_idea_number(db, number)
    if not obj: return None
    obj.status='used'; obj.used_at=datetime.utcnow(); db.commit(); db.refresh(obj); return obj

def send_telegram_message(text: str) -> bool:
    s=get_settings()
    if not s.telegram_bot_token or not s.telegram_chat_id:
        logger.warning("Telegram env missing; not sent")
        return False
    url=f"https://api.telegram.org/bot{s.telegram_bot_token}/sendMessage"
    ok=True
    for chunk in split_telegram_message(text):
        sent=False
        for attempt in range(3):
            try:
                r=httpx.post(url, json={"chat_id": s.telegram_chat_id, "text": chunk}, timeout=20)
                r.raise_for_status(); sent=True; break
            except Exception as exc:
                status = getattr(getattr(exc, 'response', None), 'status_code', None)
                body = ''
                try:
                    body = str(exc.response.json())[:300]
                except Exception:
                    body = str(exc)[:300]
                logger.warning("telegram send failed attempt %s status=%s body=%s", attempt+1, status, body)
        ok = ok and sent
        if not sent:
            break
    return ok

def send_report(db: Session, report: DailyReport | None) -> bool:
    if not report:
        logger.warning("No report available to send")
        return False
    ok=send_telegram_message(report.telegram_message or "")
    if ok:
        report.telegram_sent_at=datetime.utcnow(); db.commit()
    return ok

def handle_command(db: Session, text: str) -> str:
    cmd=(text or "").strip()
    if is_agent_os_command(cmd):
        return render_agent_os_command(db, cmd)
    if cmd.startswith('/caption'):
        idea=get_idea_from_today(db, parse_number_arg(cmd)); return render_caption_response(idea) if idea else "ไม่พบไอเดียลำดับนี้"
    if cmd.startswith('/carousel'):
        idea=get_idea_from_today(db, parse_number_arg(cmd)); return render_carousel_response(idea) if idea else "ไม่พบไอเดียลำดับนี้"
    if cmd.startswith('/reels'):
        idea=get_idea_from_today(db, parse_number_arg(cmd)); return render_reels_response(idea) if idea else "ไม่พบไอเดียลำดับนี้"
    if cmd.startswith('/post_plan'):
        return "โพสต์เช้า\nเป้าหมาย: Inbox\nHook: คอมช้าอย่าเพิ่งซื้อใหม่\nรูปแบบ: ภาพเดี่ยว/เช็กลิสต์\nCaption สั้น: ส่งอาการมาให้แอดช่วยดูได้\nCTA: ทักเพจ Advice สามร้อยยอด\n\nโพสต์บ่าย\nเป้าหมาย: ให้ความรู้\nHook: RAM กับ SSD อัปอะไรก่อนดี\nรูปแบบ: Carousel\nCaption สั้น: เลือกให้ตรงอาการ ประหยัดกว่า\nCTA: ส่งรุ่นมาให้ดูได้\n\nโพสต์เย็น\nเป้าหมาย: Reels\nHook: WiFi หลุดบ่อยแก้ยังไง\nรูปแบบ: คลิป 30 วิ\nCaption สั้น: บ้าน/ร้านเน็ตหลุด ทักมาปรึกษาได้\nCTA: Advice สามร้อยยอด"
    if cmd.startswith('/more'):
        r=db.query(DailyReport).order_by(DailyReport.report_date.desc()).first(); return (r.telegram_message + "\n\nรายละเอียดเพิ่ม: เลือกไอเดียที่ตรงสินค้าหน้าร้านก่อน และเลี่ยงมุมที่ขายของต่อไม่ได้") if r else "ยังไม่มีรายงาน"
    if cmd.startswith('/save_idea'):
        number=parse_number_arg(cmd); obj=save_idea_number(db, number)
        return f"บันทึกไอเดียลำดับ {number} แล้วครับ" if obj else "ไม่พบไอเดียลำดับนี้"
    if cmd.startswith('/used'):
        number=parse_number_arg(cmd); obj=mark_idea_used(db, number)
        return f"ทำเครื่องหมายว่าใช้ไอเดียลำดับ {number} แล้วครับ" if obj else "ไม่พบไอเดียลำดับนี้"
    return render_agent_os_help_fallback()


def render_agent_os_help_fallback() -> str:
    return "คำสั่งที่ใช้ได้: /status /today /radar /aging /planner /promos /canva_preview /caption 1 /carousel 1 /reels 1 /post_plan /save_idea 1 /used 1 /more"
