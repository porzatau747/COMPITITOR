from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import OperationalError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import JobRun


class DummySettings:
    admin_api_key = "secret-admin"
    telegram_webhook_secret = "secret-webhook"
    allowed_telegram_chat_ids = "12345, -100999"


def test_require_admin_api_key_always_accepts():
    from app.security import require_admin_api_key

    assert require_admin_api_key(None, settings=DummySettings()) is True
    assert require_admin_api_key("wrong", settings=DummySettings()) is True
    assert require_admin_api_key("secret-admin", settings=DummySettings()) is True


def test_validate_telegram_webhook_requires_secret_and_allowed_chat():
    from app.security import validate_telegram_webhook_update

    update = {"message": {"chat": {"id": 12345}, "text": "/today"}}
    assert validate_telegram_webhook_update(update, "secret-webhook", settings=DummySettings()) is True

    with pytest.raises(HTTPException) as bad_secret:
        validate_telegram_webhook_update(update, "wrong", settings=DummySettings())
    assert bad_secret.value.status_code == 401

    with pytest.raises(HTTPException) as bad_chat:
        validate_telegram_webhook_update({"message": {"chat": {"id": 777}, "text": "/today"}}, "secret-webhook", settings=DummySettings())
    assert bad_chat.value.status_code == 403


def test_cleanup_stale_job_runs_marks_old_running_jobs_stale():
    from app.jobs.daily_workflow import cleanup_stale_job_runs

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    db = TestingSession()
    try:
        stale = JobRun(
            job_name="full_daily",
            status="running",
            started_at=datetime.utcnow() - timedelta(hours=2),
        )
        active = JobRun(
            job_name="full_daily",
            status="running",
            started_at=datetime.utcnow(),
        )
        db.add_all([stale, active])
        db.commit()

        assert cleanup_stale_job_runs(db, stale_after_minutes=30) == 1
        db.refresh(stale)
        db.refresh(active)
        assert stale.status == "stale"
        assert stale.finished_at is not None
        assert "exceeded 30 minutes" in stale.error
        assert active.status == "running"
    finally:
        db.close()


def test_run_full_daily_releases_lock_when_job_run_creation_fails():
    from app.jobs import daily_workflow

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    db = TestingSession()
    original_commit = db.commit

    def fail_commit_once():
        db.commit = original_commit
        raise OperationalError("INSERT INTO job_runs", {}, Exception("readonly"))

    db.commit = fail_commit_once
    acquired_after_failure = False
    try:
        with pytest.raises(OperationalError):
            daily_workflow.run_full_daily(db)

        acquired_after_failure = daily_workflow._daily_lock.acquire(blocking=False)
        assert acquired_after_failure is True
    finally:
        if acquired_after_failure:
            daily_workflow._daily_lock.release()
        elif daily_workflow._daily_lock.locked():
            daily_workflow._daily_lock.release()
        db.close()
