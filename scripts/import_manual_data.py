import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.collectors.manual_import_collector import ManualImportCollector
from app.database import SessionLocal, init_db
from app.services.scoring_service import average_raw_score, score_post
from app.models import Post


def main():
    parser = argparse.ArgumentParser(description="Import manual CSV/JSON posts, including Facebook page exports")
    parser.add_argument("path", help="CSV or JSON file path")
    parser.add_argument("--score", action="store_true")
    args = parser.parse_args()

    init_db()
    db = SessionLocal()
    try:
        imported = ManualImportCollector().import_file(db, args.path)
        if args.score:
            posts = db.query(Post).all()
            avg = average_raw_score(posts)
            for post in posts:
                score_post(post, average_raw=avg)
            db.commit()
        print(f"imported={imported}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
