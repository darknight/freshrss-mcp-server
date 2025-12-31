"""Custom exceptions for FreshRSS MCP Server."""


class FreshRSSError(Exception):
    """Base exception for FreshRSS MCP Server."""


class AuthenticationError(FreshRSSError):
    """Failed to authenticate with FreshRSS API."""


class APIError(FreshRSSError):
    """FreshRSS API returned an error.

    Attributes:
        status_code: HTTP status code from the API response.
    """

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class ArticleNotFoundError(FreshRSSError):
    """Requested article was not found.

    Attributes:
        article_id: The ID of the article that was not found.
    """

    def __init__(self, article_id: str) -> None:
        super().__init__(f"Article not found: {article_id}")
        self.article_id = article_id


class FetchError(FreshRSSError):
    """Failed to fetch full article content from URL.

    Attributes:
        url: The URL that failed to fetch.
    """

    def __init__(self, url: str, reason: str | None = None) -> None:
        message = f"Failed to fetch article from: {url}"
        if reason:
            message += f" ({reason})"
        super().__init__(message)
        self.url = url


class ConfigurationError(FreshRSSError):
    """Invalid or missing configuration."""
