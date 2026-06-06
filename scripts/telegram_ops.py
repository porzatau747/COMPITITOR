from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"


def load_env() -> dict[str, str]:
    values: dict[str, str] = {}
    if ENV_PATH.exists():
        for raw in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    values.update({k: v for k, v in os.environ.items() if k.startswith("TELEGRAM_") or k in {"PUBLIC_WEBHOOK_URL"}})
    return values


def bot_api_url(token: str, method: str) -> str:
    return f"https://api.telegram.org/bot{token}/{method}"


def require_token(values: dict[str, str]) -> str:
    token = values.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit("missing TELEGRAM_BOT_TOKEN")
    return token


def print_json(label: str, payload: object) -> None:
    print(f"{label}=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


def cmd_check(args: argparse.Namespace) -> int:
    values = load_env()
    token = require_token(values)
    chat_id = values.get("TELEGRAM_CHAT_ID", "").strip()

    me = httpx.get(bot_api_url(token, "getMe"), timeout=20)
    print("GETME_STATUS", me.status_code)
    print_json("GETME", me.json())

    webhook = httpx.get(bot_api_url(token, "getWebhookInfo"), timeout=20)
    result = webhook.json().get("result", {})
    print_json(
        "WEBHOOK_INFO",
        {
            "url_set": bool(result.get("url")),
            "url": result.get("url") or "",
            "pending_update_count": result.get("pending_update_count"),
            "last_error_date": result.get("last_error_date"),
            "last_error_message": result.get("last_error_message"),
        },
    )

    if args.send_test:
        if not chat_id:
            raise SystemExit("missing TELEGRAM_CHAT_ID")
        sent = httpx.post(
            bot_api_url(token, "sendMessage"),
            json={"chat_id": chat_id, "text": args.message},
            timeout=20,
        )
        print("SEND_STATUS", sent.status_code)
        print_json("SEND", sent.json())
    return 0


def cmd_set_webhook(args: argparse.Namespace) -> int:
    values = load_env()
    token = require_token(values)
    secret = values.get("TELEGRAM_WEBHOOK_SECRET", "").strip()
    url = (args.url or values.get("PUBLIC_WEBHOOK_URL") or "").strip()
    if not url:
        raise SystemExit("missing webhook URL: pass --url https://.../telegram/webhook or set PUBLIC_WEBHOOK_URL")
    if not url.startswith("https://"):
        raise SystemExit("Telegram requires an HTTPS webhook URL")
    if not secret:
        raise SystemExit("missing TELEGRAM_WEBHOOK_SECRET")

    response = httpx.post(
        bot_api_url(token, "setWebhook"),
        json={
            "url": url,
            "secret_token": secret,
            "allowed_updates": ["message", "edited_message"],
            "drop_pending_updates": args.drop_pending_updates,
        },
        timeout=20,
    )
    print("SET_WEBHOOK_STATUS", response.status_code)
    print_json("SET_WEBHOOK", response.json())
    return 0 if response.status_code == 200 and response.json().get("ok") else 1


def cmd_delete_webhook(args: argparse.Namespace) -> int:
    values = load_env()
    token = require_token(values)
    response = httpx.post(
        bot_api_url(token, "deleteWebhook"),
        json={"drop_pending_updates": args.drop_pending_updates},
        timeout=20,
    )
    print("DELETE_WEBHOOK_STATUS", response.status_code)
    print_json("DELETE_WEBHOOK", response.json())
    return 0 if response.status_code == 200 and response.json().get("ok") else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Telegram Bot API operations for Advice Content Radar")
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check", help="Validate getMe, webhook info, and optionally send a test message")
    check.add_argument("--send-test", action="store_true")
    check.add_argument("--message", default="ทดสอบจาก Advice Content Radar: Telegram พร้อมใช้งานครับ")
    check.set_defaults(func=cmd_check)

    set_webhook = sub.add_parser("set-webhook", help="Register HTTPS webhook with Telegram")
    set_webhook.add_argument("--url", help="Public HTTPS URL ending with /telegram/webhook")
    set_webhook.add_argument("--drop-pending-updates", action="store_true")
    set_webhook.set_defaults(func=cmd_set_webhook)

    delete_webhook = sub.add_parser("delete-webhook", help="Remove webhook")
    delete_webhook.add_argument("--drop-pending-updates", action="store_true")
    delete_webhook.set_defaults(func=cmd_delete_webhook)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
