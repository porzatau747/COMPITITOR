from datetime import date, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.models import DailyReport, JobRun, Post, SavedIdea, Source


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


def test_ops_summary_marks_stale_running_job(db_session):
    from app.services.ops_summary_service import build_ops_summary

    db_session.add(
        JobRun(
            job_name="full_daily",
            status="running",
            started_at=datetime.utcnow() - timedelta(hours=2),
        )
    )
    db_session.commit()

    summary = build_ops_summary(db_session)

    assert summary["latest_job"]["status"] == "stale"
    assert any(issue["title"] == "Daily workflow stuck" for issue in summary["top_issues"])


def test_ops_summary_marks_report_outdated_and_telegram_not_sent(db_session):
    from app.services.ops_summary_service import build_ops_summary

    db_session.add(
        DailyReport(
            report_date=date.today() - timedelta(days=1),
            telegram_message="brief",
            top_posts=[],
            telegram_sent_at=None,
        )
    )
    db_session.commit()

    summary = build_ops_summary(db_session)

    assert summary["report"]["status"] == "outdated"
    assert summary["telegram"]["status"] == "not_sent"
    assert any(issue["title"] == "Report outdated" for issue in summary["top_issues"])
    assert any(issue["title"] == "Telegram not sent" for issue in summary["top_issues"])


def test_ops_summary_counts_source_health(db_session):
    from app.services.ops_summary_service import build_ops_summary

    ok_source = Source(
        name="Active With Posts",
        platform="facebook",
        source_url="https://example.com/ok",
        source_type="competitor",
        active=True,
    )
    empty_source = Source(
        name="Empty Source",
        platform="facebook",
        source_url="https://example.com/empty",
        source_type="competitor",
        active=True,
    )
    inactive_source = Source(
        name="Inactive Source",
        platform="facebook",
        source_url="https://example.com/inactive",
        source_type="competitor",
        active=False,
    )
    db_session.add_all([ok_source, empty_source, inactive_source])
    db_session.flush()
    db_session.add(
        Post(
            source_id=ok_source.id,
            post_url="https://example.com/post",
            post_text="Notebook sale",
            collected_at=datetime.utcnow(),
        )
    )
    db_session.commit()

    summary = build_ops_summary(db_session)

    assert summary["sources"]["total"] == 3
    assert summary["sources"]["ok"] == 1
    assert summary["sources"]["empty"] == 1
    assert summary["sources"]["inactive"] == 1


def test_ops_summary_includes_saved_idea_counts(db_session):
    from app.services.ops_summary_service import build_ops_summary

    db_session.add_all(
        [
            SavedIdea(idea_number=1, title="RAM upgrade", status="saved"),
            SavedIdea(idea_number=2, title="Printer care", status="used"),
        ]
    )
    db_session.commit()

    summary = build_ops_summary(db_session)

    assert summary["saved_ideas"]["total"] == 2
    assert summary["saved_ideas"]["saved"] == 1
    assert summary["saved_ideas"]["used"] == 1
    assert summary["saved_ideas"]["items"][0]["title"] == "Printer care"


def test_ops_summary_api_returns_dashboard_contract(db_session):
    from fastapi.testclient import TestClient

    from app.main import app

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = TestClient(app).get("/ops/summary")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert set(response.json()) == {
        "latest_job",
        "sources",
        "report",
        "telegram",
        "saved_ideas",
        "production",
        "top_issues",
    }


def test_source_update_can_disable_source_with_partial_payload(db_session):
    from fastapi.testclient import TestClient

    from app.main import app

    source = Source(
        name="Disable Me",
        platform="facebook",
        source_url="https://example.com/disable-me",
        source_type="competitor",
        active=True,
    )
    db_session.add(source)
    db_session.commit()

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = TestClient(app).put(f"/sources/{source.id}", json={"active": False})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["active"] is False


def test_ops_summary_masks_production_secret_values(db_session, monkeypatch):
    from app.config import Settings
    from app.services.ops_summary_service import build_ops_summary

    settings = Settings(
        admin_api_key="secret-admin",
        telegram_webhook_secret="secret-webhook",
        allowed_telegram_chat_ids="12345",
        telegram_bot_token="secret-token",
        telegram_chat_id="secret-chat",
        database_url="postgresql+psycopg://user:secret-pass@localhost/db",
    )
    monkeypatch.setattr("app.services.ops_summary_service.get_settings", lambda: settings)

    summary = build_ops_summary(db_session)
    summary_text = str(summary)

    assert "secret-admin" not in summary_text
    assert "secret-webhook" not in summary_text
    assert "secret-token" not in summary_text
    assert "secret-chat" not in summary_text
    assert "secret-pass" not in summary_text
    assert summary["production"]["checks"][0]["configured"] is True
    assert summary["production"]["checks"][-1]["kind"] == "postgresql"
