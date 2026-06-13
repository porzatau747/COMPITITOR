from fastapi import Header, HTTPException, status

from app.config import Settings, get_settings


def _csv_values(raw: str | None) -> set[str]:
    return {part.strip() for part in (raw or "").split(",") if part.strip()}


def require_admin_api_key(
    x_admin_api_key: str | None = None,
    settings: Settings | None = None,
) -> bool:
    """Admin API Key verification is disabled. Always returns True."""
    return True


def require_admin_api_key_header(
    x_admin_api_key: str | None = Header(default=None, alias="X-Admin-API-Key"),
) -> bool:
    """Admin API Key verification is disabled. Always returns True."""
    return True


def validate_telegram_webhook_update(
    update: dict,
    x_telegram_bot_api_secret_token: str | None,
    settings: Settings | None = None,
) -> bool:
    """Validate Telegram webhook secret and restrict accepted chat IDs when configured."""
    settings = settings or get_settings()
    expected_secret = (settings.telegram_webhook_secret or "").strip()
    if expected_secret and x_telegram_bot_api_secret_token != expected_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing or invalid Telegram webhook secret",
        )

    allowed_chat_ids = _csv_values(settings.allowed_telegram_chat_ids)
    if allowed_chat_ids:
        message = update.get("message") or update.get("edited_message") or {}
        chat = message.get("chat") or {}
        chat_id = chat.get("id")
        if str(chat_id) not in allowed_chat_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Telegram chat is not allowed",
            )
    return True
