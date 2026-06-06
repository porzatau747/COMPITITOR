from pydantic import BaseModel

class ReportOut(BaseModel):
    id: int
    report_date: object
    summary: str | None
    top_posts: list | None
    recommended_actions: dict | None
    best_hooks: list | None
    telegram_message: str | None
    class Config: from_attributes = True
