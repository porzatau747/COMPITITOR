import argparse
import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, insert, select
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.database import Base
from app import models  # noqa: F401 - registers models with Base metadata

DEFAULT_SQLITE_URL = "sqlite:///./advice_content_radar.db"


def copy_table(source: Session, target: Session, table, dry_run: bool) -> tuple[str, int, int]:
    rows = [dict(row._mapping) for row in source.execute(select(table)).all()]
    existing_ids = {row[0] for row in target.execute(select(table.c.id)).all()} if "id" in table.c else set()
    rows_to_copy = [row for row in rows if row.get("id") not in existing_ids]
    if not dry_run and rows_to_copy:
        target.execute(insert(table), rows_to_copy)
    return table.name, len(rows), len(rows_to_copy)


def main():
    parser = argparse.ArgumentParser(description="Copy local SQLite data to PostgreSQL")
    parser.add_argument("--sqlite-url", default=os.getenv("SQLITE_DATABASE_URL", DEFAULT_SQLITE_URL))
    parser.add_argument("--postgres-url", default=os.getenv("POSTGRES_DATABASE_URL"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.postgres_url:
        raise SystemExit("POSTGRES_DATABASE_URL or --postgres-url is required")

    source_engine = create_engine(args.sqlite_url, connect_args={"check_same_thread": False})
    target_engine = create_engine(args.postgres_url, pool_pre_ping=True)
    Base.metadata.create_all(bind=target_engine)

    with Session(source_engine) as source, Session(target_engine) as target:
        copied = []
        for table in Base.metadata.sorted_tables:
            copied.append(copy_table(source, target, table, dry_run=args.dry_run))
        if not args.dry_run:
            target.commit()

    mode = "dry_run" if args.dry_run else "copied"
    print(f"mode={mode}")
    for table_name, source_count, new_count in copied:
        print(f"{table_name}: source_rows={source_count} rows_to_copy={new_count}")


if __name__ == "__main__":
    main()
