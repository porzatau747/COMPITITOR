from datetime import datetime
from pydantic import BaseModel

class PostOut(BaseModel):
    id: int
    source_id: int | None
    post_url: str
    post_text: str | None
    like_count: int
    comment_count: int
    share_count: int
    view_count: int
    raw_viral_score: float
    normalized_score: float
    local_relevance_score: float
    final_score: float
    detected_product_category: str | None = None
    posted_at: datetime | None = None
    class Config: from_attributes = True
