import logging
from fastapi import Depends, FastAPI, Header
from sqlalchemy.orm import Session
from app.database import init_db, get_db
from app.routers import sources, posts, reports, ideas, jobs
from app.security import require_admin_api_key_header, validate_telegram_webhook_update
from app.services.telegram_service import handle_command
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
app=FastAPI(title="Advice Content Radar", version="0.1.0")
@app.on_event("startup")
def startup(): init_db()
@app.get("/health")
def health(): return {"ok": True, "service": "Advice Content Radar"}
@app.post("/telegram/webhook")
def telegram_webhook(
    update: dict,
    db: Session=Depends(get_db),
    x_telegram_bot_api_secret_token: str | None = Header(default=None, alias="X-Telegram-Bot-Api-Secret-Token"),
):
    validate_telegram_webhook_update(update, x_telegram_bot_api_secret_token)
    msg=(update.get('message') or {}).get('text') or ''
    return {"reply": handle_command(db,msg)}
app.include_router(sources.router, dependencies=[Depends(require_admin_api_key_header)]); app.include_router(posts.router, dependencies=[Depends(require_admin_api_key_header)]); app.include_router(reports.router, dependencies=[Depends(require_admin_api_key_header)]); app.include_router(ideas.router, dependencies=[Depends(require_admin_api_key_header)]); app.include_router(jobs.router, dependencies=[Depends(require_admin_api_key_header)])

from fastapi.staticfiles import StaticFiles
import os
static_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
app.mount("/dashboard", StaticFiles(directory=static_path, html=True), name="static")

