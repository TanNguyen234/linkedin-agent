"""Unit tests for config, models, and errors."""
from linkedin_agent_suite.core.config import get_settings
from linkedin_agent_suite.core.models import Profile, Job

def test_settings_load():
    settings = get_settings(reload=True)
    assert settings.app_env in ("development", "production", "test")
    assert settings.data_dir.exists()

def test_models():
    p = Profile(full_name="Alice", headline="AI Engineer")
    assert "Alice" in p.full_text()
    j = Job(id="1", title="Dev", company="Co", url="http://x")
    assert j.title == "Dev"
