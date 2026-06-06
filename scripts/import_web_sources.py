import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.collectors.web_agent_collector import WebAgentCollector
from app.database import SessionLocal, init_db
from app.services.scoring_service import score_post

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")


def main() -> int:
    parser = argparse.ArgumentParser(description="Import public web pages into Advice Content Radar")
    parser.add_argument("--config", default="data/web_sources.json", help="JSON config with public web sources")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay between detail-page requests per source")
    parser.add_argument("--no-robots-check", action="store_true", help="Disable robots.txt check (not recommended)")
    parser.add_argument("--score", action="store_true", help="Score imported posts immediately")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        raise SystemExit(f"Config not found: {config_path}")

    init_db()
    db = SessionLocal()
    try:
        collector = WebAgentCollector(
            config_path=config_path,
            delay_seconds=args.delay,
            check_robots=not args.no_robots_check,
        )
        posts = collector.collect(db)
        if args.score:
            for post in posts:
                score_post(post)
            db.commit()
        print(f"imported={len(posts)}")
        for post in posts[:10]:
            print(f"- post_id={post.id} url={post.post_url}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
