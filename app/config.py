from functools import lru_cache
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "sqlite:///./advice_content_radar.db"
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None
    openai_api_key: str | None = None
    ai_api_key: str | None = None
    ai_base_url: str | None = None
    ai_model: str = "gpt-4o-mini"
    facebook_page_access_token: str | None = None
    facebook_cookie_c_user: str | None = None
    facebook_cookie_xs: str | None = None
    admin_api_key: str | None = None
    telegram_webhook_secret: str | None = None
    allowed_telegram_chat_ids: str | None = None
    stale_job_after_minutes: int = 60
    timezone: str = "Asia/Bangkok"
    mock_mode: bool = True
    backup_ai_api_key: str | None = None
    backup_ai_base_url: str | None = "https://ws-cjzdjpjulzhupzez.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1"
    backup_ai_model: str = "qwen-plus"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("timezone", mode="before")
    @classmethod
    def default_timezone_when_blank(cls, value):
        return value or "Asia/Bangkok"

@lru_cache
def get_settings() -> Settings:
    return Settings()
