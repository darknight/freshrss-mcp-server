"""Configuration management for FreshRSS MCP Server."""

import os
from functools import lru_cache
from typing import Literal

from pydantic import model_validator
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
    mcp_transport: Literal["stdio", "sse", "streamable-http"] = "sse"
    mcp_host: str = "::"  # Listen on all interfaces (IPv4 + IPv6)
    mcp_port: int = 8080

    @model_validator(mode="before")
    @classmethod
    def use_railway_port(cls, data: dict) -> dict:
        """Use Railway's PORT if MCP_PORT is not explicitly set."""
        # Railway injects PORT, we prefer MCP_PORT but fallback to PORT
        if "mcp_port" not in data and "MCP_PORT" not in os.environ:
            railway_port = os.environ.get("PORT")
            if railway_port:
                data["mcp_port"] = int(railway_port)
        return data

    # Logging Configuration
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # API Authentication (optional)
    # If set, requires Authorization: Bearer <api_key> header
    api_key: str | None = None

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
