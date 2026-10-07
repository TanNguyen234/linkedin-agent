"""Unified configuration management."""
from __future__ import annotations

from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Global configuration settings for LinkedIn Agent Suite."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = Field(default="development", description="Application environment")
    data_dir: Path = Field(default=Path("data"), description="Path to data directory")
    logs_dir: Path = Field(default=Path("logs"), description="Path to logs directory")

    # Browser & Automation
    browser_executable: str | None = Field(default=None, description="Path to custom Chrome / Edge binary")
    browser_user_data_dir: Path = Field(
        default=Path("data/browser_profile"),
        description="Directory for persistent browser session & cookies",
    )
    headless: bool = Field(default=True, description="Run browser in headless mode")
    browser_timeout_ms: int = Field(default=30000, description="Default page navigation timeout in ms")
    slow_mo_ms: int = Field(default=100, description="Delay between actions in ms")
    require_action_confirmation: bool = Field(
        default=True,
        description="Whether write actions require explicit interactive approval",
    )

    # Official LinkedIn API
    linkedin_access_token: str = Field(default="", description="OAuth token with w_member_social scope")
    enable_official_posting: bool = Field(default=False, description="Explicit flag allowing official API posts")
    linkedin_api_version: str = Field(default="202506", description="LinkedIn REST API Version header")

    # Content Auto-publish Guardrails
    autopublish_enabled: bool = Field(default=False, description="Autonomous post publishing (strictly OFF by default)")
    max_posts_per_day: int = Field(default=2, description="Daily publishing budget cap")

    # LLM Provider Configuration
    llm_provider: str = Field(default="mock", description="LLM provider: gemini, openai, local, or mock")
    llm_model: str = Field(default="default", description="Model name")
    llm_api_key: str = Field(default="", description="LLM API key")

    # Job Intelligence APIs
    remotive_api_url: str = Field(default="https://remotive.com/api/remote-jobs", description="Remotive API URL")
    remoteok_api_url: str = Field(default="https://remoteok.com/api", description="RemoteOK API URL")
    default_target_role: str = Field(default="agentic-ai-systems-engineer", description="Default role")

    def resolve_paths(self, base_dir: Path | None = None) -> None:
        root = base_dir or Path.cwd()
        if not self.data_dir.is_absolute():
            self.data_dir = (root / self.data_dir).resolve()
        if not self.logs_dir.is_absolute():
            self.logs_dir = (root / self.logs_dir).resolve()
        if not self.browser_user_data_dir.is_absolute():
            self.browser_user_data_dir = (root / self.browser_user_data_dir).resolve()

_cached_settings: Settings | None = None

def get_settings(reload: bool = False) -> Settings:
    global _cached_settings
    if _cached_settings is None or reload:
        _cached_settings = Settings()
        _cached_settings.resolve_paths()
        _cached_settings.data_dir.mkdir(parents=True, exist_ok=True)
        _cached_settings.logs_dir.mkdir(parents=True, exist_ok=True)
        _cached_settings.browser_user_data_dir.mkdir(parents=True, exist_ok=True)
    return _cached_settings
