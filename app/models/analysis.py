from sqlalchemy import DateTime, ForeignKey, Integer, JSON, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Analysis(Base):
    __tablename__ = "analyses"
    __table_args__ = (UniqueConstraint("post_id", name="uq_analyses_post_id"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"))
    hook: Mapped[str | None] = mapped_column(Text)
    hook_type: Mapped[list | None] = mapped_column(JSON)
    content_type: Mapped[str | None] = mapped_column(Text)
    pain_point: Mapped[str | None] = mapped_column(Text)
    engagement_trigger: Mapped[list | None] = mapped_column(JSON)
    why_it_worked: Mapped[str | None] = mapped_column(Text)
    risk: Mapped[list | None] = mapped_column(JSON)
    local_angle: Mapped[str | None] = mapped_column(Text)
    suggested_hook: Mapped[str | None] = mapped_column(Text)
    caption_draft: Mapped[str | None] = mapped_column(Text)
    creative_direction: Mapped[str | None] = mapped_column(Text)
    sales_bridge: Mapped[str | None] = mapped_column(Text)
    cta: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[object] = mapped_column(DateTime, server_default=func.now())
    post = relationship("Post", back_populates="analysis")
