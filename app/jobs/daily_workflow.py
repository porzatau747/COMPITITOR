import logging
from datetime import datetime, timedelta
from threading import Lock
from sqlalchemy.orm import Session
from app.config import get_settings
from app.models import Post, JobRun
from app.services.collector_service import collect_recent_posts
from app.services.scoring_service import score_post, average_raw_score
from app.services.memory_service import recent_idea_texts
from app.services.report_service import analyze_top_posts, generate_daily_report
from app.services.telegram_service import send_report
logger=logging.getLogger(__name__)
_daily_lock=Lock()


def cleanup_stale_job_runs(db: Session, stale_after_minutes: int = 60) -> int:
    cutoff = datetime.utcnow() - timedelta(minutes=stale_after_minutes)
    stale_runs = (
        db.query(JobRun)
        .filter(JobRun.status == "running", JobRun.started_at < cutoff)
        .all()
    )
    for run in stale_runs:
        run.status = "stale"
        run.finished_at = datetime.utcnow()
        run.error = f"Job exceeded {stale_after_minutes} minutes and was marked stale before a new run"
    if stale_runs:
        db.commit()
        logger.warning("marked %s stale running job(s)", len(stale_runs))
    return len(stale_runs)


def run_collect(db: Session) -> dict:
    return {"collected": collect_recent_posts(db, 24)}

def run_score(db: Session) -> dict:
    recent=recent_idea_texts(db)
    posts=db.query(Post).all(); count=0
    average_raw=average_raw_score(posts)
    for p in posts:
        score_post(p, average_raw=average_raw, recent_ideas=recent); count+=1
    db.commit(); logger.info("scored %s posts", count); return {"scored": count}

def run_analyze(db: Session) -> dict:
    count=analyze_top_posts(db, 5); logger.info("analyzed %s posts", count); return {"analyzed": count}

def run_generate_report(db: Session) -> dict:
    report=generate_daily_report(db); logger.info("report generated id=%s", report.id); return {"report_id": report.id, "message": report.telegram_message}

def run_full_daily(db: Session, send: bool = False) -> dict:
    stale_count = cleanup_stale_job_runs(db, get_settings().stale_job_after_minutes)
    if not _daily_lock.acquire(blocking=False):
        return {"skipped": "daily workflow already running"}
    run=JobRun(job_name="full_daily", status="running")
    db.add(run); db.commit(); db.refresh(run)
    try:
        out={"stale_jobs_marked": stale_count}; out.update(run_collect(db)); out.update(run_score(db)); out.update(run_analyze(db)); out.update(run_generate_report(db))
        if send:
            from app.models import DailyReport
            r=db.get(DailyReport, out["report_id"]); out["telegram_sent"]=send_report(db, r)
        run.status="success"; run.result={k:v for k,v in out.items() if k != "message"}; run.finished_at=datetime.utcnow(); db.commit()
        out["job_run_id"]=run.id
        return out
    except Exception as exc:
        db.rollback()
        run.status="error"; run.error=str(exc)[:1000]; run.finished_at=datetime.utcnow(); db.add(run); db.commit()
        raise
    finally:
        _daily_lock.release()
