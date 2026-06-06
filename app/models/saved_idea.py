from sqlalchemy import DateTime, ForeignKey, Integer, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class SavedIdea(Base):
    __tablename__ = "saved_ideas"
    __table_args__ = (UniqueConstraint("report_id", "idea_number", name="uq_saved_ideas_report_number"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_id: Mapped[int | None] = mapped_column(ForeignKey("daily_reports.id"))
    post_id: Mapped[int | None] = mapped_column(ForeignKey("posts.id"))
    idea_number: Mapped[int | None] = mapped_column(Integer)
    title: Mapped[str | None] = mapped_column(Text)
    local_angle: Mapped[str | None] = mapped_column(Text)
    suggested_hook: Mapped[str | None] = mapped_column(Text)
    caption_draft: Mapped[str | None] = mapped_column(Text)
    creative_direction: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default="saved")
    created_at: Mapped[object] = mapped_column(DateTime, server_default=func.now())
    used_at: Mapped[object | None] = mapped_column(DateTime)
