import logging
from sqlalchemy.orm import Session
from app.config import get_settings
from app.collectors.mock_collector import MockCollector
from app.collectors.web_agent_collector import WebAgentCollector
from app.collectors.facebook_graph_collector import FacebookGraphCollector
from app.collectors.facebook_cloak_collector import FacebookCloakCollector
logger=logging.getLogger(__name__)

def collect_recent_posts(db: Session, hours: int = 24) -> int:
    try:
        settings=get_settings()
        if settings.mock_mode:
            posts=MockCollector().collect(db, hours=hours)
        else:
            posts=[]
            # WebAgentCollector and FacebookGraphCollector are disabled per competitor page restrictions
            # posts.extend(WebAgentCollector().collect(db, hours=hours))
            # posts.extend(FacebookGraphCollector().collect(db, hours=hours))
            posts.extend(FacebookCloakCollector().collect(db, hours=hours))
            if not posts:
                logger.info("collectors found no new public/authorized posts; keeping existing database content")
        logger.info("collector imported %s new posts", len(posts))
        return len(posts)
    except Exception:
        logger.exception("collector failed")
        raise
