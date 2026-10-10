"""Configuration management for LinkedIn Agent Suite."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_env: str = Field(default="development", alias="APP_ENV")
    logs_dir: Path = Field(default_factory=lambda: Path("data/logs"), alias="LOGS_DIR")
    data_dir: Path = Field(default_factory=lambda: Path("data"), alias="DATA_DIR")
    browser_user_data_dir: Path = Field(
        default_factory=lambda: Path("data/browser_profile"),
        alias="BROWSER_USER_DATA_DIR",
    )
    browser_headless: bool = Field(default=True, alias="BROWSER_HEADLESS")
    browser_slow_mo_ms: int = Field(default=50, alias="BROWSER_SLOW_MO_MS")
    browser_timeout_ms: int = Field(default=30000, alias="BROWSER_TIMEOUT_MS")

    # Official API Configuration
    enable_official_posting: bool = Field(
        default=False, alias="ENABLE_OFFICIAL_POSTING"
    )
    linkedin_access_token: str | None = Field(
        default=None, alias="LINKEDIN_ACCESS_TOKEN"
    )
    linkedin_author_urn: str | None = Field(default=None, alias="LINKEDIN_AUTHOR_URN")
    linkedin_api_version: str = Field(default="202609", alias="LINKEDIN_API_VERSION")
    require_action_confirmation: bool = Field(
        default=True, alias="REQUIRE_ACTION_CONFIRMATION"
    )

    # LLM Configuration
    llm_provider: str = Field(default="mock", alias="LLM_PROVIDER")
    llm_model: str = Field(default="gemini-2.5-flash", alias="LLM_MODEL")
    llm_api_key: str | None = Field(default=None, alias="LLM_API_KEY")
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")

    # Autopublish Guardrails
    autopublish_enabled: bool = Field(default=False, alias="AUTOPUBLISH_ENABLED")
    max_posts_per_day: int = Field(default=2, alias="MAX_POSTS_PER_DAY")
    allowed_posting_start: int = Field(default=8, alias="ALLOWED_POSTING_START")
    allowed_posting_end: int = Field(default=18, alias="ALLOWED_POSTING_END")
    min_content_score: float = Field(default=75.0, alias="MIN_CONTENT_SCORE")
    min_evidence_score: float = Field(default=80.0, alias="MIN_EVIDENCE_SCORE")
    topic_cooldown_days: int = Field(default=7, alias="TOPIC_COOLDOWN_DAYS")

    approval_hmac_secret: str | None = Field(default=None, alias="APPROVAL_HMAC_SECRET")



_settings_instance: Settings | None = None


def get_settings(reload: bool = False) -> Settings:
    global _settings_instance
    if reload or _settings_instance is None:
        _settings_instance = Settings()
        _settings_instance.data_dir.mkdir(parents=True, exist_ok=True)
        _settings_instance.browser_user_data_dir.mkdir(parents=True, exist_ok=True)
    return _settings_instance
