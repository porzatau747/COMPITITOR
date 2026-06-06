from pydantic import BaseModel
class TelegramUpdate(BaseModel):
    update_id: int | None = None
    message: dict | None = None
