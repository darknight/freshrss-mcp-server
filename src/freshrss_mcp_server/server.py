"""FreshRSS MCP Server - Main entry point."""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from freshrss_mcp_server import __version__
from freshrss_mcp_server.api.client import FreshRSSClient
from freshrss_mcp_server.config import get_settings
from freshrss_mcp_server.tools import articles, fetcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("freshrss-mcp")

# Initialize MCP server
mcp = FastMCP("freshrss")

# Global client instance (initialized lazily)
_client: FreshRSSClient | None = None


async def get_client() -> FreshRSSClient:
    """Get or create FreshRSS API client.

    Returns:
        Initialized FreshRSSClient instance.
    """
    global _client
    if _client is None:
        settings = get_settings()
        _client = FreshRSSClient(
            api_url=settings.freshrss_api_url,
            username=settings.freshrss_username,
            password=settings.freshrss_api_password,
            timeout=settings.request_timeout,
        )
        logger.info("FreshRSS client initialized for %s", settings.freshrss_api_url)
    return _client


# =============================================================================
# MCP Tools Registration
# =============================================================================


@mcp.tool()
async def get_unread_articles(
    limit: int = 100,
    feed_id: str | None = None,
) -> list[dict[str, Any]]:
    """Fetch unread articles from FreshRSS.

    Use this tool to get a list of unread articles from your RSS subscriptions.
    Each article includes title, summary, link, and publication date.

    Args:
        limit: Maximum number of articles to return (default: 100)
        feed_id: Optional feed ID to filter articles by specific subscription

    Returns:
        List of articles with id, title, summary, link, published, feed_title
    """
    client = await get_client()
    return await articles.get_unread_articles(client, limit=limit, feed_id=feed_id)


@mcp.tool()
async def get_article_content(article_id: str) -> dict[str, Any]:
    """Get full content of a specific article.

    Use this tool to retrieve the complete content of a single article
    when you need more details than the summary provides.

    Args:
        article_id: The article ID to fetch (from get_unread_articles)

    Returns:
        Article with full content including id, title, content, link, published
    """
    client = await get_client()
    return await articles.get_article_content(client, article_id=article_id)


@mcp.tool()
async def mark_as_read(article_ids: list[str]) -> dict[str, Any]:
    """Mark articles as read in FreshRSS.

    Use this tool after processing articles to mark them as read.
    This helps keep track of which articles have been reviewed.

    Args:
        article_ids: List of article IDs to mark as read

    Returns:
        Operation result with success status and count of articles marked
    """
    client = await get_client()
    return await articles.mark_as_read(client, article_ids=article_ids)


@mcp.tool()
async def get_subscriptions() -> list[dict[str, Any]]:
    """Get all RSS feed subscriptions with unread counts.

    Use this tool to see all your RSS subscriptions and how many
    unread articles each feed has.

    Returns:
        List of subscriptions with id, title, url, unread_count, category
    """
    client = await get_client()
    return await articles.get_subscriptions(client)


@mcp.tool()
async def fetch_full_article(url: str) -> dict[str, Any]:
    """Fetch full article content from original URL.

    Use this tool when an RSS feed only provides a summary and you need
    the complete article text. It extracts the main content from the webpage.

    Args:
        url: The original article URL to fetch

    Returns:
        Extracted article content with title, text, author, and date if available
    """
    settings = get_settings()
    return await fetcher.fetch_full_article(url, timeout=settings.request_timeout)


# =============================================================================
# Entry Point
# =============================================================================


def main() -> None:
    """Run the FreshRSS MCP server."""
    logger.info("Starting FreshRSS MCP Server v%s", __version__)
    mcp.run()


if __name__ == "__main__":
    main()
