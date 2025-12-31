"""MCP tools for FreshRSS operations."""

from freshrss_mcp_server.tools.articles import (
    get_article_content,
    get_subscriptions,
    get_unread_articles,
    mark_as_read,
)
from freshrss_mcp_server.tools.fetcher import fetch_full_article

__all__ = [
    "fetch_full_article",
    "get_article_content",
    "get_subscriptions",
    "get_unread_articles",
    "mark_as_read",
]
