from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

from app.database import init_db, SessionLocal
from app.jobs.daily_workflow import run_full_daily

init_db()
db = SessionLocal()
try:
    out = run_full_daily(db, send=True)
    if not out.get("telegram_sent"):
        # Fallback for Hermes cron delivery if the Telegram Bot API cannot reach the chat yet.
        print("⚠️ Advice Content Radar สร้างรายงานแล้ว แต่ Telegram Bot API ยังส่งไม่สำเร็จ")
        print("สาเหตุที่พบบ่อย: ยังไม่ได้กด Start กับบอท หรือ TELEGRAM_CHAT_ID ไม่ใช่ chat id ของบอทนี้")
        print()
        print(out.get("message", ""))
finally:
    db.close()
