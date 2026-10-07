"""Central configuration system using Pydantic Settings and dotenv."""

from __future__ import annotations

import os
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

    # Browser & Automation
    browser_executable: str | None = Field(default=None, description="Path to custom Chrome / Edge binary")
    browser_user_data_dir: Path = Field(
        default=Path("data/browser_profile"),
        description="Directory for persistent browser session & cookies",
    )
    headless: bool = Field(default=False, description="Run browser in headless mode (default: headed)")
    browser_timeout_ms: int = Field(default=30000, description="Default page navigation timeout in ms")
    slow_mo_ms: int = Field(default=100, description="Delay between actions to mimic human interaction")

    # Safety & Human-In-The-Loop
    require_action_confirmation: bool = Field(
        default=True,
        description="Whether write/destructive actions require explicit interactive approval",
    )

    # Storage & Paths
    data_dir: Path = Field(default=Path("data"), description="Path to data directory")
    logs_dir: Path = Field(default=Path("logs"), description="Path to logs directory")

    # Job Intelligence APIs
    remotive_api_url: str = Field(
        default="https://remotive.com/api/remote-jobs",
        description="Public Remotive API endpoint",
    )
    remoteok_api_url: str = Field(
        default="https://remoteok.com/api",
        description="Public RemoteOK API endpoint",
    )

    # Defaults
    default_target_role: str = Field(
        default="agentic-ai-systems-engineer",
        description="Default role for profile audits and optimizations",
    )

    def resolve_paths(self, base_dir: Path | None = None) -> None:
        """Resolve all relative paths against the provided base directory."""
        root = base_dir or Path.cwd()
        if not self.data_dir.is_absolute():
            self.data_dir = (root / self.data_dir).resolve()
        if not self.logs_dir.is_absolute():
            self.logs_dir = (root / self.logs_dir).resolve()
        if not self.browser_user_data_dir.is_absolute():
            self.browser_user_data_dir = (root / self.browser_user_data_dir).resolve()


_cached_settings: Settings | None = None


def get_settings(reload: bool = False) -> Settings:
    """Get the active configuration settings singleton."""
    global _cached_settings
    if _cached_settings is None or reload:
        _cached_settings = Settings()
        _cached_settings.resolve_paths()
        # Ensure directories exist
        _cached_settings.data_dir.mkdir(parents=True, exist_ok=True)
        _cached_settings.logs_dir.mkdir(parents=True, exist_ok=True)
        _cached_settings.browser_user_data_dir.mkdir(parents=True, exist_ok=True)
    return _cached_settings
