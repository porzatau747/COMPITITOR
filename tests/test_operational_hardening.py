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


def test_api_key_pool_parsing(monkeypatch):
    from app.services.ai_analyzer_service import _get_api_keys
    from app.config import Settings
    
    mock_settings = Settings(
        ai_api_key="key1, key2\nkey3 ,key4",
        mock_mode=False
    )
    monkeypatch.setattr("app.services.ai_analyzer_service.get_settings", lambda: mock_settings)
    
    keys = _get_api_keys()
    assert keys == ["key1", "key2", "key3", "key4"]


def test_api_key_pool_rotation_on_failure(monkeypatch):
    from app.services.ai_analyzer_service import analyze_post_with_ai
    import app.services.ai_analyzer_service as ai_service
    from app.config import Settings
    
    ai_service._current_key_index = 0
    
    mock_settings = Settings(
        ai_api_key="bad_key1, bad_key2",
        ai_base_url="https://generativelanguage.googleapis.com",
        ai_model="gemini-2.5-flash",
        mock_mode=False
    )
    monkeypatch.setattr("app.services.ai_analyzer_service.get_settings", lambda: mock_settings)
    
    called_keys = []
    
    def mock_analyze_gemini(prompt, key, base_url, model):
        called_keys.append(key)
        if key == "bad_key1":
            raise RuntimeError("Gemini API error status=429 body=Quota exceeded")
        return {
            "hook": "Test Hook",
            "hook_type": ["Pain Hook"],
            "content_type": "IT",
            "pain_point": "None",
            "engagement_trigger": [],
            "why_it_worked": "Simple",
            "risk": [],
            "detected_product_category": ["IT"]
        }
        
    monkeypatch.setattr("app.services.ai_analyzer_service._analyze_with_gemini", mock_analyze_gemini)
    
    class MockPost:
        post_text = "Notebook specification upgrades"
        like_count = 10
        comment_count = 5
        share_count = 2
        view_count = 0
        
    post = MockPost()
    res = analyze_post_with_ai(post, "Test Page")
    
    assert called_keys == ["bad_key1", "bad_key2"]
    assert res["hook"] == "Test Hook"
    assert ai_service._current_key_index == 1


def test_backup_api_key_fallback_on_all_primary_keys_failure(monkeypatch):
    import json
    from app.services.ai_analyzer_service import analyze_post_with_ai
    import app.services.ai_analyzer_service as ai_service
    from app.config import Settings
    
    ai_service._current_key_index = 0
    
    mock_settings = Settings(
        ai_api_key="bad_key1",
        ai_base_url="https://generativelanguage.googleapis.com",
        ai_model="gemini-2.5-flash",
        backup_ai_api_key="good_backup_key",
        backup_ai_base_url="https://backup.maas.aliyuncs.com/v1",
        backup_ai_model="backup-qwen-plus",
        mock_mode=False
    )
    monkeypatch.setattr("app.services.ai_analyzer_service.get_settings", lambda: mock_settings)
    
    # Mock primary key generator to fail
    def mock_analyze_gemini(prompt, key, base_url, model):
        raise RuntimeError("Gemini key error status=429 Quota Exceeded")
    monkeypatch.setattr("app.services.ai_analyzer_service._analyze_with_gemini", mock_analyze_gemini)
    
    # Mock openai client that is used for backup key
    called_backup_client_args = []
    called_backup_completions_args = []
    
    class MockChatCompletionsMessage:
        content = json.dumps({
            "hook": "Backup Hook",
            "hook_type": ["Question Hook"],
            "content_type": "IT Upgrade",
            "pain_point": "High Price",
            "engagement_trigger": [],
            "why_it_worked": "Simple explanation",
            "risk": [],
            "detected_product_category": ["Upgrade"],
            "local_angle": "Draft",
            "suggested_hook": "Hook",
            "caption_draft": "Draft",
            "creative_direction": "Dir",
            "sales_bridge": "Bridge",
            "cta": "Call"
        })
        
    class MockChatCompletionsChoice:
        message = MockChatCompletionsMessage()
        
    class MockChatCompletionsResponse:
        choices = [MockChatCompletionsChoice()]
        
    class MockChatCompletions:
        def create(self, **kwargs):
            called_backup_completions_args.append(kwargs)
            return MockChatCompletionsResponse()
            
    class MockChat:
        completions = MockChatCompletions()
        
    class MockOpenAI:
        def __init__(self, **kwargs):
            called_backup_client_args.append(kwargs)
            self.chat = MockChat()
            
    monkeypatch.setattr("app.services.ai_analyzer_service.OpenAI", MockOpenAI)
    
    class MockPost:
        post_text = "Primary key failure test"
        like_count = 10
        comment_count = 5
        share_count = 2
        view_count = 0
        
    post = MockPost()
    res = analyze_post_with_ai(post, "Test Page")
    
    assert len(called_backup_client_args) == 1
    assert called_backup_client_args[0]["api_key"] == "good_backup_key"
    assert called_backup_client_args[0]["base_url"] == "https://backup.maas.aliyuncs.com/v1"
    assert len(called_backup_completions_args) == 1
    assert called_backup_completions_args[0]["model"] == "backup-qwen-plus"
    assert res["hook"] == "Backup Hook"

