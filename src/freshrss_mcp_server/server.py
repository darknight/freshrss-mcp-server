"""FreshRSS MCP Server - Main entry point."""

import argparse
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


def create_server(host: str = "127.0.0.1", port: int = 8000) -> FastMCP:
    """Create and configure the MCP server with all tools.

    Args:
        host: Host to bind for HTTP mode
        port: Port for HTTP mode

    Returns:
        Configured FastMCP server instance
    """
    server = FastMCP("freshrss", host=host, port=port)

    # Register all tools
    @server.tool()
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

    @server.tool()
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

    @server.tool()
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

    @server.tool()
    async def get_subscriptions() -> list[dict[str, Any]]:
        """Get all RSS feed subscriptions with unread counts.

        Use this tool to see all your RSS subscriptions and how many
        unread articles each feed has.

        Returns:
            List of subscriptions with id, title, url, unread_count, category
        """
        client = await get_client()
        return await articles.get_subscriptions(client)

    @server.tool()
    async def fetch_full_article(url: str) -> dict[str, Any]:
        """Fetch full article content from original URL.

        Use this tool when an RSS feed only provides a summary and you need
        the complete article text. It extracts the main content from the webpage.

        Args:
            url: The original article URL to fetch

        Returns:
            Extracted article content with title, text, author, and date if available
        """
        app_settings = get_settings()
        return await fetcher.fetch_full_article(url, timeout=app_settings.request_timeout)

    return server


# Default server instance for module-level access
mcp = create_server()


# =============================================================================
# Entry Point
# =============================================================================


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    CLI arguments override environment variable settings.
    """
    # Get defaults from config (environment variables)
    settings = get_settings()

    parser = argparse.ArgumentParser(
        description="FreshRSS MCP Server - Connect AI applications to FreshRSS",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"freshrss-mcp {__version__}",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default=settings.mcp_transport,
        help=f"Transport mode (default: {settings.mcp_transport}, env: MCP_TRANSPORT)",
    )
    parser.add_argument(
        "--host",
        default=settings.mcp_host,
        help=f"Host to bind HTTP server (default: {settings.mcp_host}, env: MCP_HOST)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=settings.mcp_port,
        help=f"Port for HTTP server (default: {settings.mcp_port}, env: MCP_PORT)",
    )
    return parser.parse_args()


def main() -> None:
    """Run the FreshRSS MCP server."""
    args = parse_args()

    logger.info("Starting FreshRSS MCP Server v%s", __version__)
    logger.info("Transport: %s", args.transport)

    if args.transport == "stdio":
        # Use default server for STDIO mode
        mcp.run()
    else:
        # Create new server with custom host/port for SSE mode
        server = create_server(host=args.host, port=args.port)
        logger.info("HTTP Server: http://%s:%d", args.host, args.port)
        logger.info("SSE endpoint: http://%s:%d/sse", args.host, args.port)
        server.run(transport="sse")


if __name__ == "__main__":
    main()
