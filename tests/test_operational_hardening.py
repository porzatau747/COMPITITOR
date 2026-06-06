from types import SimpleNamespace

from app.collectors.manual_import_collector import _safe_int
from app.collectors.web_agent_collector import _is_safe_public_url
from app.services.scoring_service import average_raw_score
from app.services.telegram_service import split_telegram_message


def test_average_raw_score_uses_real_engagement_values():
    posts = [
        SimpleNamespace(like_count=10, comment_count=0, share_count=0, view_count=0),
        SimpleNamespace(like_count=20, comment_count=0, share_count=0, view_count=0),
    ]
    assert average_raw_score(posts) == 15


def test_manual_import_safe_int_handles_blank_and_bad_values():
    assert _safe_int("") == 0
    assert _safe_int(None) == 0
    assert _safe_int(" 7 ") == 7
    assert _safe_int("bad") == 0


def test_web_agent_rejects_private_or_local_urls():
    assert not _is_safe_public_url("http://localhost:8000/private")
    assert not _is_safe_public_url("http://127.0.0.1:8000/private")
    assert not _is_safe_public_url("http://192.168.1.1/admin")
    assert _is_safe_public_url("https://www.blognone.com/")


def test_telegram_message_split_preserves_text_under_limit():
    text = "A" * 5000
    chunks = split_telegram_message(text, limit=4096)
    assert len(chunks) == 2
    assert all(len(chunk) <= 4096 for chunk in chunks)
    assert "".join(chunks) == text
