import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.database import SessionLocal, init_db
from app.services.source_health_service import build_source_health_report


def main():
    parser = argparse.ArgumentParser(description="Print source health for Advice Content Radar")
    parser.add_argument("--stale-hours", type=int, default=72)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    init_db()
    db = SessionLocal()
    try:
        rows = build_source_health_report(db, stale_hours=args.stale_hours)
    finally:
        db.close()

    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return

    print(f"source_count={len(rows)} stale_hours={args.stale_hours}")
    for row in rows:
        print(
            f"[{row['health_status']}] id={row['source_id']} posts={row['post_count']} "
            f"latest={row['latest_collected_at']} name={row['name']} reason={row['reason']}"
        )


if __name__ == "__main__":
    main()
