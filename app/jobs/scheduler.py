from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.config import get_settings
from app.database import SessionLocal
from app.jobs.daily_workflow import run_full_daily

scheduler=BackgroundScheduler(timezone=get_settings().timezone)


def _with_db(fn):
    db=SessionLocal()
    try: return fn(db)
    finally: db.close()


def start_scheduler():
    if scheduler.running:
        return
    scheduler.add_job(
        lambda: _with_db(lambda db: run_full_daily(db, send=True)),
        CronTrigger(hour=6, minute=0),
        id="advice_content_radar_full_daily",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
