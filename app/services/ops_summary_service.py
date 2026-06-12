from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import DailyReport, JobRun, SavedIdea
from app.services.source_health_service import build_source_health_report


def _iso(value) -> str | None:
    return value.isoformat() if value else None


def _issue(code: str, title: str, severity: str, detail: str | None = None) -> dict:
    return {
        "code": code,
        "title": title,
        "severity": severity,
        "detail": detail,
    }


def _latest_job_summary(db: Session, stale_job_after_minutes: int, issues: list[dict]) -> dict:
    job = db.query(JobRun).order_by(JobRun.id.desc()).first()
    if not job:
        return {
            "name": None,
            "status": "none",
            "started_at": None,
            "finished_at": None,
            "error": None,
        }

    status = job.status
    if job.status == "running" and job.started_at:
        stale_before = datetime.utcnow() - timedelta(minutes=stale_job_after_minutes)
        if job.started_at < stale_before:
            status = "stale"
            issues.append(
                _issue(
                    "stale_job",
                    "Daily workflow stuck",
                    "error",
                    f"Job has been running longer than {stale_job_after_minutes} minutes.",
                )
            )

    if status == "error":
        issues.append(_issue("job_error", "Latest job failed", "error", job.error))

    return {
        "name": job.job_name,
        "status": status,
        "started_at": _iso(job.started_at),
        "finished_at": _iso(job.finished_at),
        "error": job.error,
    }


def _source_summary(db: Session, issues: list[dict]) -> dict:
    items = build_source_health_report(db)
    counts = {"ok": 0, "empty": 0, "stale": 0, "inactive": 0}
    for item in items:
        status = item["health_status"]
        if status in counts:
            counts[status] += 1

    empty_items = [item for item in items if item["health_status"] == "empty"]
    stale_items = [item for item in items if item["health_status"] == "stale"]
    if empty_items:
        issues.append(
            _issue(
                "empty_source",
                "Empty sources need review",
                "warning",
                f"{len(empty_items)} source(s) have no posts.",
            )
        )
    if stale_items:
        issues.append(
            _issue(
                "stale_source",
                "Stale sources need review",
                "warning",
                f"{len(stale_items)} source(s) have not updated recently.",
            )
        )

    return {
        "total": len(items),
        **counts,
        "items": items,
    }


def _report_summary(db: Session, issues: list[dict]) -> tuple[dict, dict]:
    report = db.query(DailyReport).order_by(DailyReport.report_date.desc(), DailyReport.id.desc()).first()
    if not report:
        issues.append(_issue("report_missing", "No report yet", "warning", None))
        return (
            {
                "status": "missing",
                "report_date": None,
                "message_length": 0,
                "top_posts_count": 0,
            },
            {"status": "no_report", "sent_at": None},
        )

    report_status = "ok"
    if report.report_date != date.today():
        report_status = "outdated"
        issues.append(
            _issue(
                "report_outdated",
                "Report outdated",
                "warning",
                f"Latest report date is {report.report_date.isoformat()}.",
            )
        )

    message_length = len(report.telegram_message or "")
    if message_length > 4096:
        report_status = "too_long"
        issues.append(
            _issue(
                "report_too_long",
                "Telegram brief is long",
                "warning",
                f"Brief has {message_length} characters.",
            )
        )

    telegram_status = "sent" if report.telegram_sent_at else "not_sent"
    if telegram_status == "not_sent":
        issues.append(_issue("telegram_not_sent", "Telegram not sent", "warning", None))

    return (
        {
            "status": report_status,
            "report_date": report.report_date.isoformat(),
            "message_length": message_length,
            "top_posts_count": len(report.top_posts or []),
        },
        {"status": telegram_status, "sent_at": _iso(report.telegram_sent_at)},
    )


def _saved_ideas_summary(db: Session) -> dict:
    ideas = db.query(SavedIdea).order_by(SavedIdea.id.desc()).limit(5).all()
    total = db.query(SavedIdea).count()
    saved = db.query(SavedIdea).filter(SavedIdea.status == "saved").count()
    used = db.query(SavedIdea).filter(SavedIdea.status == "used").count()
    return {
        "total": total,
        "saved": saved,
        "used": used,
        "items": [
            {
                "id": idea.id,
                "idea_number": idea.idea_number,
                "title": idea.title,
                "status": idea.status,
                "used_at": _iso(idea.used_at),
            }
            for idea in ideas
        ],
    }


def _production_checks() -> dict:
    settings = get_settings()
    checks = [
        {"key": "ADMIN_API_KEY", "configured": bool(settings.admin_api_key)},
        {"key": "TELEGRAM_WEBHOOK_SECRET", "configured": bool(settings.telegram_webhook_secret)},
        {"key": "ALLOWED_TELEGRAM_CHAT_IDS", "configured": bool(settings.allowed_telegram_chat_ids)},
        {"key": "TELEGRAM_BOT_TOKEN", "configured": bool(settings.telegram_bot_token)},
        {"key": "TELEGRAM_CHAT_ID", "configured": bool(settings.telegram_chat_id)},
        {
            "key": "DATABASE_URL",
            "configured": bool(settings.database_url),
            "type": "sqlite" if settings.database_url.startswith("sqlite") else "external",
        },
    ]
    return {"checks": checks}


def build_ops_summary(
    db: Session,
    stale_job_after_minutes: int | None = None,
) -> dict:
    settings = get_settings()
    stale_minutes = stale_job_after_minutes or settings.stale_job_after_minutes
    issues: list[dict] = []

    latest_job = _latest_job_summary(db, stale_minutes, issues)
    sources = _source_summary(db, issues)
    report, telegram = _report_summary(db, issues)
    saved_ideas = _saved_ideas_summary(db)
    production = _production_checks()

    for check in production["checks"]:
        if not check["configured"] and check["key"] != "DATABASE_URL":
            issues.append(
                _issue(
                    "missing_config",
                    f"{check['key']} missing",
                    "warning",
                    "Configuration is not set.",
                )
            )

    return {
        "latest_job": latest_job,
        "sources": sources,
        "report": report,
        "telegram": telegram,
        "saved_ideas": saved_ideas,
        "production": production,
        "top_issues": issues,
    }
