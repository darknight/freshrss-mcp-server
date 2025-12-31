"""Article-related MCP tools for FreshRSS."""

import logging
from typing import Any

from freshrss_mcp_server.api.client import FreshRSSClient
from freshrss_mcp_server.api.models import ArticleResponse, SubscriptionResponse
from freshrss_mcp_server.exceptions import APIError, FreshRSSError

logger = logging.getLogger(__name__)


async def get_unread_articles(
    client: FreshRSSClient,
    limit: int = 100,
    feed_id: str | None = None,
) -> list[dict[str, Any]]:
    """Fetch unread articles from FreshRSS.

    Args:
        client: FreshRSS API client
        limit: Maximum number of articles to return (default: 100)
        feed_id: Optional feed ID to filter articles by specific subscription

    Returns:
        List of articles with id, title, summary, link, published, feed_title, feed_id
    """
    try:
        articles = await client.get_unread_articles(limit=limit, feed_id=feed_id)
        return [
            ArticleResponse.from_article(article).model_dump(mode="json") for article in articles
        ]
    except APIError as e:
        logger.error("Failed to get unread articles: %s", e)
        return [{"error": True, "message": str(e), "code": "API_ERROR"}]
    except FreshRSSError as e:
        logger.error("FreshRSS error: %s", e)
        return [{"error": True, "message": str(e), "code": "FRESHRSS_ERROR"}]


async def get_article_content(
    client: FreshRSSClient,
    article_id: str,
) -> dict[str, Any]:
    """Get full content of a specific article.

    Args:
        client: FreshRSS API client
        article_id: The article ID to fetch

    Returns:
        Article with full content including id, title, content, link, published
    """
    try:
        # Get the article by fetching stream contents with the specific article
        # The article_id in Google Reader API is like "tag:google.com,2005:reader/item/..."
        stream = await client.get_stream_contents(
            stream_id="user/-/state/com.google/reading-list",
            count=1000,  # Fetch more to find the article
        )

        for article in stream.items:
            if article.id == article_id:
                return {
                    "id": article.id,
                    "title": article.title,
                    "content": article.summary.content if article.summary else "",
                    "link": article.link,
                    "published": article.published_at.isoformat(),
                    "feed_title": article.origin.title if article.origin else "",
                    "feed_id": article.origin.stream_id if article.origin else "",
                }

        return {"error": True, "message": f"Article not found: {article_id}", "code": "NOT_FOUND"}

    except APIError as e:
        logger.error("Failed to get article content: %s", e)
        return {"error": True, "message": str(e), "code": "API_ERROR"}
    except FreshRSSError as e:
        logger.error("FreshRSS error: %s", e)
        return {"error": True, "message": str(e), "code": "FRESHRSS_ERROR"}


async def mark_as_read(
    client: FreshRSSClient,
    article_ids: list[str],
) -> dict[str, Any]:
    """Mark articles as read.

    Args:
        client: FreshRSS API client
        article_ids: List of article IDs to mark as read

    Returns:
        Operation result with success status and count of articles marked
    """
    if not article_ids:
        return {"success": True, "marked_count": 0, "message": "No articles to mark"}

    try:
        success = await client.mark_as_read(article_ids)
        if success:
            return {
                "success": True,
                "marked_count": len(article_ids),
                "message": f"Successfully marked {len(article_ids)} article(s) as read",
            }
        else:
            return {
                "success": False,
                "marked_count": 0,
                "message": "Failed to mark articles as read",
            }
    except APIError as e:
        logger.error("Failed to mark articles as read: %s", e)
        return {"error": True, "message": str(e), "code": "API_ERROR"}
    except FreshRSSError as e:
        logger.error("FreshRSS error: %s", e)
        return {"error": True, "message": str(e), "code": "FRESHRSS_ERROR"}


async def get_subscriptions(
    client: FreshRSSClient,
) -> list[dict[str, Any]]:
    """Get all RSS feed subscriptions with unread counts.

    Args:
        client: FreshRSS API client

    Returns:
        List of subscriptions with id, title, url, unread_count, category
    """
    try:
        subscriptions = await client.get_subscriptions()
        unread_counts = await client.get_unread_counts()

        return [
            SubscriptionResponse.from_subscription(
                sub, unread_count=unread_counts.get(sub.id, 0)
            ).model_dump(mode="json")
            for sub in subscriptions
        ]
    except APIError as e:
        logger.error("Failed to get subscriptions: %s", e)
        return [{"error": True, "message": str(e), "code": "API_ERROR"}]
    except FreshRSSError as e:
        logger.error("FreshRSS error: %s", e)
        return [{"error": True, "message": str(e), "code": "FRESHRSS_ERROR"}]
