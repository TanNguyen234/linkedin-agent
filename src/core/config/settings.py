"""Unified configuration management."""
import os
from pydantic_settings import BaseSettings
from pydantic import Field
from src.core.errors.exceptions import ConfigurationError

class Settings(BaseSettings):
    app_env: str = Field(default="development", env="APP_ENV")
    data_dir: str = Field(default="data", env="DATA_DIR")
    logs_dir: str = Field(default="logs", env="LOGS_DIR")
    browser_headless: bool = Field(default=True, env="BROWSER_HEADLESS")
    browser_executable_path: str = Field(default="", env="CHROME_PATH")
    browser_user_data_dir: str = Field(default="data/browser_profile", env="BROWSER_USER_DATA_DIR")
    
    # Official API config (Optional)
    linkedin_access_token: str = Field(default="", env="LINKEDIN_ACCESS_TOKEN")
    enable_official_posting: bool = Field(default=False, env="ENABLE_OFFICIAL_POSTING")
    
    # Content Auto-publish guard (OFF by default)
    autopublish_enabled: bool = Field(default=False, env="AUTOPUBLISH_ENABLED")
    max_posts_per_day: int = Field(default=2, env="MAX_POSTS_PER_DAY")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

def get_settings() -> Settings:
    settings = Settings()
    # Check for forbidden secrets in file
    return settings
