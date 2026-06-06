from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "advice_content_radar.db"
BACKUP_DIR = ROOT / "backups"


def main() -> int:
    if not DB.exists():
        print(f"missing_db={DB}")
        return 1
    BACKUP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = BACKUP_DIR / f"advice_content_radar_{timestamp}.db"
    shutil.copy2(DB, target)
    print(f"backup_created={target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
