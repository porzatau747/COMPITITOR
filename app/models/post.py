from sqlalchemy import DateTime, Float, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Post(Base):
    __tablename__ = "posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"))
    post_url: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    post_text: Mapped[str | None] = mapped_column(Text)
    media_url: Mapped[str | None] = mapped_column(Text)
    posted_at: Mapped[object | None] = mapped_column(DateTime)
    collected_at: Mapped[object] = mapped_column(DateTime, server_default=func.now())
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    comment_count: Mapped[int] = mapped_column(Integer, default=0)
    share_count: Mapped[int] = mapped_column(Integer, default=0)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    raw_viral_score: Mapped[float] = mapped_column(Float, default=0)
    normalized_score: Mapped[float] = mapped_column(Float, default=0)
    local_relevance_score: Mapped[float] = mapped_column(Float, default=0)
    final_score: Mapped[float] = mapped_column(Float, default=0)
    detected_product_category: Mapped[str | None] = mapped_column(Text)
    detected_content_type: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[object] = mapped_column(DateTime, server_default=func.now())
    source = relationship("Source", back_populates="posts")
    analysis = relationship("Analysis", back_populates="post", uselist=False)
