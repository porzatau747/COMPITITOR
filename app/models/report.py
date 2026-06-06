from sqlalchemy import Date, DateTime, Integer, JSON, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class DailyReport(Base):
    __tablename__ = "daily_reports"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_date: Mapped[object] = mapped_column(Date, unique=True, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    top_posts: Mapped[list | None] = mapped_column(JSON)
    recommended_actions: Mapped[dict | None] = mapped_column(JSON)
    best_hooks: Mapped[list | None] = mapped_column(JSON)
    telegram_message: Mapped[str | None] = mapped_column(Text)
    telegram_sent_at: Mapped[object | None] = mapped_column(DateTime)
    created_at: Mapped[object] = mapped_column(DateTime, server_default=func.now())
