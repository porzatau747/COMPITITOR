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
class SourceUpdate(BaseModel):
    name: str | None = None
    platform: str | None = None
    source_url: str | None = None
    source_type: str | None = None
    category: str | None = None
    location: str | None = None
    priority_score: int | None = None
    active: bool | None = None
class SourceOut(SourceBase):
    id: int
    class Config: from_attributes = True
