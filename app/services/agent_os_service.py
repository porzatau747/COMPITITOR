import json
import logging
import os
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.models import DailyReport
from app.services.ops_summary_service import build_ops_summary

logger = logging.getLogger(__name__)

COMMANDS = {"/status", "/today", "/radar", "/aging", "/planner", "/promos", "/canva_preview"}
WEEKLY_PLANNER_ROOT = Path(os.getenv("WEEKLY_PLANNER_ROOT", r"D:\por\project app\weekly-content-planner"))
AGENT_OS_LOG_DIR = Path(os.getenv("AGENT_OS_LOG_DIR", r"D:\por\project app\compititor\logs\agent-os"))


def is_agent_os_command(text: str) -> bool:
    command = _command_name(text)
    return command in COMMANDS or command == "/help"


def render_agent_os_help() -> str:
    return (
        "คำสั่งที่ใช้ได้:\n"
        "อ่านอย่างเดียว: /status /today /radar /aging /planner /promos /canva_preview\n"
        "คอนเทนต์: /caption 1 /carousel 1 /reels 1 /more\n"
        "จัดการไอเดียเดิม: /save_idea 1 /used 1"
    )


def render_agent_os_command(db: Session | None, text: str) -> str:
    command = _command_name(text)
    ok = True
    warnings: list[str] = []
    try:
        if command == "/help":
            reply = render_agent_os_help()
        elif command == "/status":
            reply = _render_status(db, warnings)
        elif command == "/today":
            reply = _render_today(db, warnings)
        elif command == "/radar":
            reply = _render_radar(db, warnings)
        elif command == "/aging":
            reply = _render_aging(warnings)
        elif command == "/planner":
            reply = _render_planner(warnings)
        elif command == "/promos":
            reply = _render_promos(warnings)
        elif command == "/canva_preview":
            reply = _render_canva_preview(warnings)
        else:
            ok = False
            reply = render_agent_os_help()
    except Exception as exc:  # pragma: no cover - safety net for Telegram UX
        ok = False
        logger.exception("Agent OS command failed")
        reply = "ขออภัยครับ อ่านข้อมูล Agent OS ไม่สำเร็จ แต่ยังไม่มีการสั่งรันงานหรือเขียนข้อมูล\nNext: ลอง /status อีกครั้ง"
        warnings.append(type(exc).__name__)
    finally:
        _audit(command or text, ok, warnings)
    return reply


def _render_status(db: Session | None, warnings: list[str]) -> str:
    report_line = "Content Radar: ไม่ได้เชื่อมฐานข้อมูลในคำสั่งนี้"
    if db is not None:
        summary = build_ops_summary(db)
        report_line = f"Content Radar: report={summary['report']['status']}, telegram={summary['telegram']['status']}, issues={len(summary['top_issues'])}"
    planner = _load_planner_state(warnings)
    promos = _load_promotion_batches(warnings)
    planner_line = "Weekly Planner: " + _file_status_text(planner, "planner-state.json")
    promo_line = "Promos: " + _file_status_text(promos, "promotion-batches.json")
    return "\n".join([
        "สถานะระบบ Advice AI Agent OS",
        report_line,
        planner_line,
        promo_line,
        _warning_line(warnings),
        "Next: /today /radar /aging /planner /promos /canva_preview",
    ])


def _render_today(db: Session | None, warnings: list[str]) -> str:
    parts = ["รายงานวันนี้ Advice สามร้อยยอด"]
    report = _latest_report(db)
    if report and report.telegram_message:
        parts.append(_trim(report.telegram_message, 900))
    elif report and report.summary:
        parts.append(_trim(report.summary, 500))
    else:
        parts.append("Content Radar: ยังไม่มีรายงานล่าสุด")
    aging = _top_aging_items(_planner_inventory(_load_planner_state(warnings)), limit=3)
    if aging:
        parts.append("ของค้างที่ควรดันวันนี้: " + "; ".join(_format_item_short(item) for item in aging))
    batches = _extract_batches(_load_promotion_batches(warnings))
    if batches:
        parts.append(f"โปรโมชันล่าสุด: {_batch_name(batches[0])} ({_batch_status(batches[0])})")
    parts.append(_warning_line(warnings))
    parts.append("Next: /radar /aging /planner /promos")
    return "\n".join(part for part in parts if part)


def _render_radar(db: Session | None, warnings: list[str]) -> str:
    report = _latest_report(db)
    if not report:
        body = "ยังไม่มีรายงาน Content Radar ล่าสุด"
    elif report.summary:
        body = _trim(str(report.summary), 900)
    elif report.telegram_message:
        body = _trim(report.telegram_message, 900)
    else:
        body = f"พบรายงานวันที่ {report.report_date} แต่ไม่มีข้อความสรุป"
    return f"Radar Content ล่าสุด\n{body}\n{_warning_line(warnings)}\nNext: /caption 1 /carousel 1 /reels 1 /today"


def _render_aging(warnings: list[str]) -> str:
    state = _load_planner_state(warnings)
    items = _top_aging_items(_planner_inventory(state), limit=5)
    if not items:
        return f"ของค้างสต๊อก: ยังไม่พบข้อมูล aging ที่อ่านได้\n{_warning_line(warnings)}\nNext: /planner /promos"
    lines = ["ของค้างสต๊อกที่ควรดัน (อ่านอย่างเดียว)"]
    for idx, item in enumerate(items, 1):
        lines.append(f"{idx}. {_format_aging_item(item)}")
    lines.append(_warning_line(warnings))
    lines.append("Next: /promos /canva_preview")
    return "\n".join(lines)


def _render_planner(warnings: list[str]) -> str:
    state = _load_planner_state(warnings)
    inventory = _planner_inventory(state)
    if not state.get("ok"):
        return f"Weekly Planner: {state['message']}\n{_warning_line(warnings)}\nNext: /status /aging"
    total_qty = sum(_num(item.get("qty")) for item in inventory)
    aging_count = len([item for item in inventory if _num(item.get("agingDays")) >= 90])
    return "\n".join([
        "Weekly Planner snapshot (อ่านอย่างเดียว)",
        f"สินค้าใน state: {len(inventory)} รายการ / รวม qty {total_qty:g}",
        f"aging >= 90 วัน: {aging_count} รายการ",
        _warning_line(warnings),
        "Next: /aging /promos /canva_preview",
    ])


def _render_promos(warnings: list[str]) -> str:
    data = _load_promotion_batches(warnings)
    batches = _extract_batches(data)
    if not batches:
        return f"โปรโมชัน: ยังไม่พบ batch ที่อ่านได้\n{_warning_line(warnings)}\nNext: /aging /planner"
    lines = [f"โปรโมชันล่าสุด (อ่านอย่างเดียว): {len(batches)} batch"]
    for idx, batch in enumerate(batches[:5], 1):
        item_count = len(batch.get("items") or batch.get("products") or [])
        lines.append(f"{idx}. {_batch_name(batch)} | status={_batch_status(batch)} | items={item_count}")
    lines.append(_warning_line(warnings))
    lines.append("Next: /canva_preview /aging")
    return "\n".join(lines)


def _render_canva_preview(warnings: list[str]) -> str:
    data = _load_promotion_batches(warnings)
    batches = _extract_batches(data)
    if not batches:
        return f"Canva preview: ยังไม่พบ promotion batch สำหรับ preview\n{_warning_line(warnings)}\nNext: /promos /aging"
    ready = [b for b in batches if b.get("canvaCsvPath") or b.get("csvPath") or b.get("exportPath")]
    batch = ready[0] if ready else batches[0]
    readiness = "พร้อม preview ไฟล์ CSV เดิม" if ready else "ยังไม่พบ CSV path ใน batch"
    return "\n".join([
        "Canva preview (อ่านอย่างเดียว — ไม่ export ไฟล์ใหม่)",
        f"Batch: {_batch_name(batch)} ({batch.get('id') or batch.get('batchId') or '-'})",
        f"Status: {_batch_status(batch)}",
        f"ความพร้อม: {readiness}",
        _warning_line(warnings),
        "Next: /promos /planner",
    ])


def _latest_report(db: Session | None) -> DailyReport | None:
    if db is None:
        return None
    return db.query(DailyReport).order_by(DailyReport.report_date.desc(), DailyReport.id.desc()).first()


def _load_planner_state(warnings: list[str]) -> dict[str, Any]:
    return _load_json(WEEKLY_PLANNER_ROOT / "data" / "planner-state.json", warnings)


def _load_promotion_batches(warnings: list[str]) -> dict[str, Any]:
    paths = [
        WEEKLY_PLANNER_ROOT / "data" / "promotion-batches.json",
        WEEKLY_PLANNER_ROOT / "apps" / "web-app" / "data" / "promotion-batches.json",
    ]
    for path in paths:
        data = _load_json(path, warnings, warn_missing=False)
        if data.get("ok"):
            return data
    warnings.append("ยังไม่พบ promotion-batches.json")
    return {"ok": False, "message": "ยังไม่พบ promotion-batches.json"}


def _load_json(path: Path, warnings: list[str], warn_missing: bool = True) -> dict[str, Any]:
    try:
        if not path.exists():
            if warn_missing:
                warnings.append(f"ยังไม่พบ {path.name}")
            return {"ok": False, "message": f"ยังไม่พบ {path.name}", "path": str(path)}
        return {"ok": True, "path": str(path), "data": json.loads(path.read_text(encoding="utf-8"))}
    except Exception:
        warnings.append(f"อ่านข้อมูลไม่ได้: {path.name}")
        return {"ok": False, "message": f"อ่านข้อมูลไม่ได้: {path.name}", "path": str(path)}


def _planner_inventory(state: dict[str, Any]) -> list[dict[str, Any]]:
    data = state.get("data") if state.get("ok") else None
    if isinstance(data, dict):
        inventory = data.get("inventory") or data.get("items") or data.get("products")
        return inventory if isinstance(inventory, list) else []
    if isinstance(data, list):
        return data
    return []


def _top_aging_items(items: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    return sorted(
        [item for item in items if _num(item.get("agingDays") or item.get("aging_days")) > 0],
        key=lambda item: _num(item.get("agingDays") or item.get("aging_days")),
        reverse=True,
    )[:limit]


def _extract_batches(data: dict[str, Any]) -> list[dict[str, Any]]:
    payload = data.get("data") if data.get("ok") else None
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        batches = payload.get("batches") or payload.get("items") or payload.get("data")
        if isinstance(batches, list):
            return [item for item in batches if isinstance(item, dict)]
    return []


def _format_aging_item(item: dict[str, Any]) -> str:
    product = item.get("product") or item.get("name") or "ไม่ทราบชื่อสินค้า"
    code = item.get("code") or item.get("sku") or "-"
    days = _num(item.get("agingDays") or item.get("aging_days"))
    qty = _num(item.get("qty") or item.get("quantity"))
    price = item.get("sellPrice") or item.get("price")
    margin = item.get("margin")
    extras = [f"{days:g} วัน", f"qty {qty:g}"]
    if price is not None:
        extras.append(f"ราคา {price}")
    if margin is not None:
        extras.append(f"margin {margin}")
    return f"{product} [{code}] — " + ", ".join(extras)


def _format_item_short(item: dict[str, Any]) -> str:
    product = item.get("product") or item.get("name") or "สินค้า"
    days = _num(item.get("agingDays") or item.get("aging_days"))
    return f"{product} {days:g} วัน"


def _batch_name(batch: dict[str, Any]) -> str:
    return str(batch.get("name") or batch.get("title") or batch.get("id") or "ไม่ระบุชื่อ")


def _batch_status(batch: dict[str, Any]) -> str:
    return str(batch.get("status") or batch.get("state") or "unknown")


def _file_status_text(result: dict[str, Any], filename: str) -> str:
    if result.get("ok"):
        return f"พบ {filename}"
    return result.get("message") or f"ยังไม่พบ {filename}"


def _warning_line(warnings: list[str]) -> str:
    unique = []
    for item in warnings:
        if item not in unique:
            unique.append(item)
    return "คำเตือน: " + "; ".join(unique) if unique else "คำเตือน: ไม่มี"


def _trim(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _num(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _command_name(text: str) -> str:
    return (text or "").strip().split(maxsplit=1)[0].lower()


def _audit(command: str, ok: bool, warnings: list[str]) -> None:
    try:
        AGENT_OS_LOG_DIR.mkdir(parents=True, exist_ok=True)
        event = {
            "ts": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "command": command,
            "ok": ok,
            "warnings": list(dict.fromkeys(warnings))[:10],
        }
        path = AGENT_OS_LOG_DIR / f"agent-os-{datetime.now(UTC).date().isoformat()}.jsonl"
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception:
        logger.warning("Agent OS audit log write failed", exc_info=True)
