from sqlalchemy import Boolean, DateTime, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class ContentMemory(Base):
    __tablename__ = "content_memory"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    idea_text: Mapped[str | None] = mapped_column(Text)
    hook: Mapped[str | None] = mapped_column(Text)
    product_category: Mapped[str | None] = mapped_column(Text)
    content_type: Mapped[str | None] = mapped_column(Text)
    used: Mapped[bool] = mapped_column(Boolean, default=False)
    used_at: Mapped[object | None] = mapped_column(DateTime)
    created_at: Mapped[object] = mapped_column(DateTime, server_default=func.now())
