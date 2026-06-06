from pydantic import BaseModel

class SourceBase(BaseModel):
    name: str
    platform: str = "facebook"
    source_url: str
    source_type: str
    category: str | None = None
    location: str | None = None
    priority_score: int = 50
    active: bool = True

class SourceCreate(SourceBase): pass
class SourceUpdate(SourceBase): pass
class SourceOut(SourceBase):
    id: int
    class Config: from_attributes = True
