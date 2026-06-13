from datetime import date, datetime, UTC
import json

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import DailyReport


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


@pytest.fixture
def weekly_data(tmp_path, monkeypatch):
    root = tmp_path / "weekly-content-planner"
    (root / "data").mkdir(parents=True)
    (root / "apps" / "web-app" / "data").mkdir(parents=True)
    monkeypatch.setattr("app.services.agent_os_service.WEEKLY_PLANNER_ROOT", root)
    return root


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def test_agent_os_aging_reads_weekly_planner_inventory(weekly_data):
    from app.services.agent_os_service import render_agent_os_command

    write_json(
        weekly_data / "data" / "planner-state.json",
        {
            "inventory": [
                {
                    "code": "A1",
                    "product": "CONTROLLER NUBWO",
                    "qty": 2,
                    "agingDays": 266,
                    "agingBucket": "240+ days",
                    "sellPrice": 450,
                    "margin": 177,
                },
                {"code": "B2", "product": "MOUSE", "qty": 1, "agingDays": 20},
            ]
        },
    )

    text = render_agent_os_command(None, "/aging")

    assert "ของค้างสต๊อก" in text
    assert "CONTROLLER NUBWO" in text
    assert "266 วัน" in text
    assert "Next" in text


def test_agent_os_promos_and_canva_preview_read_batches(weekly_data):
    from app.services.agent_os_service import render_agent_os_command

    write_json(
        weekly_data / "apps" / "web-app" / "data" / "promotion-batches.json",
        {
            "batches": [
                {
                    "id": "batch-1",
                    "name": "Gaming clearance",
                    "status": "reviewed",
                    "items": [{"code": "A1"}, {"code": "B2"}],
                    "canvaCsvPath": "exports/batch-1.csv",
                }
            ]
        },
    )

    promos = render_agent_os_command(None, "/promos")
    canva = render_agent_os_command(None, "/canva_preview")

    assert "โปรโมชัน" in promos
    assert "Gaming clearance" in promos
    assert "Canva" in canva
    assert "batch-1" in canva
    assert "ไม่ export" in canva


def test_agent_os_status_handles_missing_weekly_files(weekly_data, db_session):
    from app.services.agent_os_service import render_agent_os_command

    text = render_agent_os_command(db_session, "/status")

    assert "สถานะระบบ" in text
    assert "Content Radar" in text
    assert "Weekly Planner" in text
    assert "ยังไม่พบ" in text


def test_agent_os_today_and_radar_use_latest_daily_report(weekly_data, db_session):
    from app.services.agent_os_service import render_agent_os_command

    db_session.add(
        DailyReport(
            report_date=date.today(),
            summary="คู่แข่งเน้นเกมมิ่งเกียร์",
            telegram_message="รายงานวันนี้: เกมมิ่งเกียร์ขายดี",
            top_posts=[{"title": "Gaming post"}],
            telegram_sent_at=datetime.now(UTC),
        )
    )
    db_session.commit()

    today = render_agent_os_command(db_session, "/today")
    radar = render_agent_os_command(db_session, "/radar")

    assert "รายงานวันนี้" in today
    assert "เกมมิ่งเกียร์" in today
    assert "Radar" in radar
    assert "เกมมิ่งเกียร์" in radar


def test_new_commands_route_through_telegram_service_without_db_writes(weekly_data, db_session):
    from app.services.telegram_service import handle_command

    statements = []

    @event.listens_for(db_session.bind, "before_cursor_execute")
    def capture_sql(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement.strip().upper())

    text = handle_command(db_session, "/status")

    assert "สถานะระบบ" in text
    assert not any(stmt.startswith(("INSERT", "UPDATE", "DELETE")) for stmt in statements)


def test_agent_os_invalid_json_returns_warning_not_exception(weekly_data):
    from app.services.agent_os_service import render_agent_os_command

    target = weekly_data / "data" / "planner-state.json"
    target.write_text("{invalid json", encoding="utf-8")

    text = render_agent_os_command(None, "/planner")

    assert "อ่านข้อมูลไม่ได้" in text
    assert "Next" in text
