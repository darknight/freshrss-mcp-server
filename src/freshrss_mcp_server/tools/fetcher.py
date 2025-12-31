"""Full article fetcher tool for FreshRSS MCP Server."""

import logging
from typing import Any

import httpx
import trafilatura

from freshrss_mcp_server.exceptions import FetchError

logger = logging.getLogger(__name__)


async def fetch_full_article(
    url: str,
    timeout: int = 30,
) -> dict[str, Any]:
    """Fetch full article content from original URL.

    Use this tool for RSS feeds that only provide summaries.
    It extracts the main article content from the webpage.

    Args:
        url: The original article URL to fetch
        timeout: Request timeout in seconds (default: 30)

    Returns:
        Extracted article content with title, text, and metadata
    """
    if not url:
        return {"error": True, "message": "URL is required", "code": "INVALID_INPUT"}

    try:
        # Fetch the webpage
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; FreshRSS-MCP/1.0)",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                },
            )
            response.raise_for_status()
            html_content = response.text

    except httpx.TimeoutException:
        logger.error("Timeout fetching URL: %s", url)
        return {"error": True, "message": f"Timeout fetching URL: {url}", "code": "TIMEOUT"}
    except httpx.HTTPStatusError as e:
        logger.error("HTTP error fetching URL %s: %s", url, e.response.status_code)
        return {
            "error": True,
            "message": f"HTTP error {e.response.status_code} fetching URL",
            "code": "HTTP_ERROR",
        }
    except httpx.RequestError as e:
        logger.error("Request error fetching URL %s: %s", url, e)
        return {"error": True, "message": f"Failed to fetch URL: {e}", "code": "REQUEST_ERROR"}

    try:
        # Extract main content using trafilatura
        extracted = trafilatura.extract(
            html_content,
            include_links=True,
            include_images=False,
            include_tables=True,
            output_format="txt",
        )

        if not extracted:
            # Try with more lenient settings
            extracted = trafilatura.extract(
                html_content,
                include_links=True,
                include_images=False,
                include_tables=True,
                output_format="txt",
                favor_recall=True,
            )

        if not extracted:
            return {
                "error": True,
                "message": "Could not extract article content from page",
                "code": "EXTRACTION_FAILED",
            }

        # Extract metadata
        metadata = trafilatura.extract_metadata(html_content)

        result: dict[str, Any] = {
            "url": url,
            "content": extracted,
        }

        if metadata:
            if metadata.title:
                result["title"] = metadata.title
            if metadata.author:
                result["author"] = metadata.author
            if metadata.date:
                result["date"] = metadata.date
            if metadata.description:
                result["description"] = metadata.description

        return result

    except Exception as e:
        logger.error("Error extracting content from %s: %s", url, e)
        raise FetchError(url, str(e)) from e
