from datetime import date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.models import DailyReport, JobRun, Post, SavedIdea, Source


@pytest.fixture()
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

    stale_job = JobRun(
        job_name="full_daily",
        status="running",
        started_at=datetime.utcnow() - timedelta(hours=2),
    )
    db_session.add(stale_job)
    db_session.commit()

    summary = build_ops_summary(db_session, stale_job_after_minutes=30)

    assert summary["latest_job"]["status"] == "stale"
    assert any(issue["code"] == "stale_job" for issue in summary["top_issues"])


def test_ops_summary_marks_report_outdated_and_telegram_not_sent(db_session):
    from app.services.ops_summary_service import build_ops_summary

    report = DailyReport(
        report_date=date.today() - timedelta(days=1),
        summary="old report",
        top_posts=[{"number": 1}, {"number": 2}],
        telegram_message="brief",
        telegram_sent_at=None,
    )
    db_session.add(report)
    db_session.commit()

    summary = build_ops_summary(db_session)

    assert summary["report"]["status"] == "outdated"
    assert summary["telegram"]["status"] == "not_sent"
    assert summary["report"]["top_posts_count"] == 2
    assert any(issue["code"] == "report_outdated" for issue in summary["top_issues"])
    assert any(issue["code"] == "telegram_not_sent" for issue in summary["top_issues"])


def test_ops_summary_counts_source_health(db_session):
    from app.services.ops_summary_service import build_ops_summary

    ok_source = Source(
        name="OK Source",
        platform="facebook_cloak",
        source_url="https://example.com/ok",
        source_type="facebook_page_public",
        active=True,
    )
    empty_source = Source(
        name="Empty Source",
        platform="facebook_cloak",
        source_url="https://example.com/empty",
        source_type="facebook_page_public",
        active=True,
    )
    inactive_source = Source(
        name="Inactive Source",
        platform="web",
        source_url="https://example.com/inactive",
        source_type="it_news_page",
        active=False,
    )
    db_session.add_all([ok_source, empty_source, inactive_source])
    db_session.flush()
    db_session.add(
        Post(
            source_id=ok_source.id,
            post_url="https://example.com/post/1",
            post_text="Notebook upgrade",
            collected_at=datetime.utcnow(),
        )
    )
    db_session.commit()

    summary = build_ops_summary(db_session)

    assert summary["sources"]["total"] == 3
    assert summary["sources"]["ok"] == 1
    assert summary["sources"]["empty"] == 1
    assert summary["sources"]["inactive"] == 1
    assert any(issue["code"] == "empty_source" for issue in summary["top_issues"])


def test_ops_summary_includes_saved_ideas(db_session):
    from app.services.ops_summary_service import build_ops_summary

    report = DailyReport(report_date=date.today(), top_posts=[], telegram_message="brief")
    db_session.add(report)
    db_session.flush()
    db_session.add_all(
        [
            SavedIdea(report_id=report.id, idea_number=1, title="RAM upgrade", status="saved"),
            SavedIdea(
                report_id=report.id,
                idea_number=2,
                title="Printer care",
                status="used",
                used_at=datetime.utcnow(),
            ),
        ]
    )
    db_session.commit()

    summary = build_ops_summary(db_session)

    assert summary["saved_ideas"]["total"] == 2
    assert summary["saved_ideas"]["saved"] == 1
    assert summary["saved_ideas"]["used"] == 1
    assert summary["saved_ideas"]["items"][0]["title"] == "Printer care"


def test_ops_summary_api_returns_dashboard_contract(db_session):
    from app.main import app

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        client = TestClient(app)
        response = client.get("/ops/summary")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) >= {
        "latest_job",
        "sources",
        "report",
        "telegram",
        "saved_ideas",
        "production",
        "top_issues",
    }


def test_source_update_can_disable_source_with_partial_payload(db_session):
    from app.main import app

    source = Source(
        name="Empty Source",
        platform="facebook_cloak",
        source_url="https://example.com/empty-disable",
        source_type="facebook_page_public",
        active=True,
    )
    db_session.add(source)
    db_session.commit()

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        client = TestClient(app)
        response = client.put(f"/sources/{source.id}", json={"active": False})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["active"] is False
