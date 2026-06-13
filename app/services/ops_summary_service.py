from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import DailyReport, JobRun, SavedIdea
from app.services.source_health_service import build_source_health_report


def build_ops_summary(db: Session) -> dict:
    settings = get_settings()
    top_issues: list[dict] = []
    latest_job = _build_latest_job(db, settings.stale_job_after_minutes, top_issues)
    sources = _build_sources(db, top_issues)
    report = _build_report(db, top_issues)
    telegram = _build_telegram(report, top_issues)
    saved_ideas = _build_saved_ideas(db)
    production = _build_production_checks(settings, top_issues)

    return {
        "latest_job": latest_job,
        "sources": sources,
        "report": report,
        "telegram": telegram,
        "saved_ideas": saved_ideas,
        "production": production,
        "top_issues": top_issues,
    }


def _build_latest_job(db: Session, stale_after_minutes: int, top_issues: list[dict]) -> dict:
    job = db.query(JobRun).order_by(JobRun.started_at.desc(), JobRun.id.desc()).first()
    if not job:
        return {"status": "none", "name": None, "started_at": None, "finished_at": None, "error": None}

    status = job.status
    if job.status == "running" and job.started_at:
        stale_before = datetime.utcnow() - timedelta(minutes=stale_after_minutes)
        if job.started_at < stale_before:
            status = "stale"
            top_issues.append({
                "title": "Daily workflow stuck",
                "severity": "error",
                "message": f"{job.job_name} has been running longer than {stale_after_minutes} minutes",
            })

    if job.status == "error":
        top_issues.append({
            "title": "Latest job failed",
            "severity": "error",
            "message": job.error or "Check job run details",
        })

    return {
        "status": status,
        "name": job.job_name,
        "started_at": _iso(job.started_at),
        "finished_at": _iso(job.finished_at),
        "error": job.error,
    }


def _build_sources(db: Session, top_issues: list[dict]) -> dict:
    items = build_source_health_report(db)
    counts = {"total": len(items), "ok": 0, "empty": 0, "stale": 0, "inactive": 0}
    for item in items:
        status = item["health_status"]
        if status in counts:
            counts[status] += 1
        if status in {"empty", "stale"}:
            top_issues.append({
                "title": "Source needs attention",
                "severity": "warning",
                "message": f"{item['name']}: {status}",
                "source_id": item["source_id"],
            })
    return {**counts, "items": items}


def _build_report(db: Session, top_issues: list[dict]) -> dict:
    report = db.query(DailyReport).order_by(DailyReport.report_date.desc(), DailyReport.id.desc()).first()
    if not report:
        top_issues.append({
            "title": "No report yet",
            "severity": "warning",
            "message": "Generate today's report before sending Telegram",
        })
        return {"status": "missing", "report_date": None, "message_length": 0, "top_posts_count": 0, "sent_at": None}

    status = "ok" if report.report_date == date.today() else "outdated"
    if status == "outdated":
        top_issues.append({
            "title": "Report outdated",
            "severity": "warning",
            "message": f"Latest report is for {report.report_date.isoformat()}",
        })

    message_length = len(report.telegram_message or "")
    if message_length > 4096:
        status = "too_long"
        top_issues.append({
            "title": "Telegram brief too long",
            "severity": "warning",
            "message": "Telegram message exceeds 4096 characters",
        })

    return {
        "status": status,
        "report_date": report.report_date.isoformat(),
        "message_length": message_length,
        "top_posts_count": len(report.top_posts or []),
        "sent_at": _iso(report.telegram_sent_at),
    }


def _build_telegram(report: dict, top_issues: list[dict]) -> dict:
    if report["status"] == "missing":
        return {"status": "no_report", "sent_at": None}
    if report["sent_at"]:
        return {"status": "sent", "sent_at": report["sent_at"]}

    top_issues.append({
        "title": "Telegram not sent",
        "severity": "warning",
        "message": "Latest report has not been sent to Telegram",
    })
    return {"status": "not_sent", "sent_at": None}


def _build_saved_ideas(db: Session) -> dict:
    ideas = db.query(SavedIdea).order_by(SavedIdea.id.desc()).limit(5).all()
    all_ideas = db.query(SavedIdea).all()
    saved_count = sum(1 for idea in all_ideas if idea.status == "saved")
    used_count = sum(1 for idea in all_ideas if idea.status == "used")
    return {
        "total": len(all_ideas),
        "saved": saved_count,
        "used": used_count,
        "items": [
            {
                "id": idea.id,
                "title": idea.title,
                "status": idea.status,
                "idea_number": idea.idea_number,
                "created_at": _iso(idea.created_at),
                "used_at": _iso(idea.used_at),
            }
            for idea in ideas
        ],
    }


def _build_production_checks(settings, top_issues: list[dict]) -> dict:
    checks = [
        {"key": "telegram_webhook_secret", "label": "TELEGRAM_WEBHOOK_SECRET configured", "configured": bool(settings.telegram_webhook_secret)},
        {"key": "allowed_telegram_chat_ids", "label": "ALLOWED_TELEGRAM_CHAT_IDS configured", "configured": bool(settings.allowed_telegram_chat_ids)},
        {"key": "telegram_delivery", "label": "Telegram token/chat id configured", "configured": bool(settings.telegram_bot_token and settings.telegram_chat_id)},
        {"key": "database_url", "label": "Database URL configured", "configured": bool(settings.database_url), "kind": _database_kind(settings.database_url)},
    ]
    for check in checks:
        if not check["configured"]:
            top_issues.append({
                "title": "Production checklist missing",
                "severity": "info",
                "message": check["label"],
                "key": check["key"],
            })
    return {"checks": checks}


def _database_kind(database_url: str) -> str:
    if database_url.startswith("postgresql"):
        return "postgresql"
    if database_url.startswith("sqlite"):
        return "sqlite"
    return "other"


def _iso(value) -> str | None:
    return value.isoformat() if value else None
