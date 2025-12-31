"""Configuration management for FreshRSS MCP Server."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # FreshRSS API Configuration
    freshrss_api_url: str
    freshrss_username: str
    freshrss_api_password: str

    # Optional settings with defaults
    request_timeout: int = 30
    default_article_limit: int = 100

    # Dynamic fetch settings (Playwright)
    enable_dynamic_fetch: bool = True
    browser_timeout: int = 30

    # MCP Server Configuration
    mcp_transport: Literal["stdio", "sse"] = "sse"
    mcp_host: str = "0.0.0.0"
    mcp_port: int = 8080

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings: Application settings loaded from environment.

    Raises:
        ValidationError: If required settings are missing.
    """
    # pydantic-settings loads required fields from environment variables
    return Settings()  # type: ignore[call-arg]


def clear_settings_cache() -> None:
    """Clear the settings cache. Useful for testing."""
    get_settings.cache_clear()
