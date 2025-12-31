"""Pydantic models for FreshRSS Google Reader API."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field, computed_field

# =============================================================================
# Authentication Models
# =============================================================================


class AuthResponse(BaseModel):
    """Response from ClientLogin endpoint."""

    sid: str = Field(alias="SID")
    lsid: str = Field(alias="LSID")
    auth: str = Field(alias="Auth")


# =============================================================================
# Subscription Models
# =============================================================================


class Category(BaseModel):
    """Feed category/folder."""

    id: str
    label: str


class Subscription(BaseModel):
    """RSS feed subscription."""

    id: str
    title: str
    url: str
    html_url: str = Field(alias="htmlUrl")
    icon_url: str | None = Field(default=None, alias="iconUrl")
    categories: list[Category] = Field(default_factory=list)


class SubscriptionList(BaseModel):
    """List of subscriptions response."""

    subscriptions: list[Subscription]


# =============================================================================
# Article Models
# =============================================================================


class ArticleOrigin(BaseModel):
    """Article source feed info."""

    stream_id: str = Field(alias="streamId")
    title: str
    html_url: str = Field(alias="htmlUrl")


class ArticleSummary(BaseModel):
    """Article summary/content."""

    content: str


class Article(BaseModel):
    """RSS article/item."""

    id: str
    title: str
    published: int  # Unix timestamp
    updated: int | None = None
    canonical: list[dict[str, Any]] = Field(default_factory=list)
    alternate: list[dict[str, Any]] = Field(default_factory=list)
    summary: ArticleSummary | None = None
    origin: ArticleOrigin | None = None

    @computed_field
    @property
    def link(self) -> str | None:
        """Get article URL from canonical or alternate links."""
        if self.canonical:
            return self.canonical[0].get("href")
        if self.alternate:
            return self.alternate[0].get("href")
        return None

    @computed_field
    @property
    def published_at(self) -> datetime:
        """Get published timestamp as datetime."""
        return datetime.fromtimestamp(self.published, tz=UTC)


class StreamContents(BaseModel):
    """Response from stream/contents endpoint."""

    id: str
    title: str | None = None
    updated: int | None = None
    items: list[Article] = Field(default_factory=list)
    continuation: str | None = None


# =============================================================================
# Unread Count Models
# =============================================================================


class UnreadCount(BaseModel):
    """Unread count for a feed/category."""

    id: str
    count: int
    newest_item_timestamp_usec: str = Field(alias="newestItemTimestampUsec")


class UnreadCountResponse(BaseModel):
    """Response from unread-count endpoint."""

    max: int
    unreadcounts: list[UnreadCount]


# =============================================================================
# MCP Tool Response Models
# =============================================================================


class ArticleResponse(BaseModel):
    """Simplified article for MCP tool response."""

    id: str
    title: str
    summary: str
    link: str | None
    published: datetime
    feed_title: str
    feed_id: str

    @classmethod
    def from_article(cls, article: Article) -> ArticleResponse:
        """Create from API Article model."""
        return cls(
            id=article.id,
            title=article.title,
            summary=article.summary.content if article.summary else "",
            link=article.link,
            published=article.published_at,
            feed_title=article.origin.title if article.origin else "",
            feed_id=article.origin.stream_id if article.origin else "",
        )


class SubscriptionResponse(BaseModel):
    """Simplified subscription for MCP tool response."""

    id: str
    title: str
    url: str
    unread_count: int = 0
    category: str | None = None

    @classmethod
    def from_subscription(
        cls, subscription: Subscription, unread_count: int = 0
    ) -> SubscriptionResponse:
        """Create from API Subscription model."""
        category = subscription.categories[0].label if subscription.categories else None
        return cls(
            id=subscription.id,
            title=subscription.title,
            url=subscription.url,
            unread_count=unread_count,
            category=category,
        )
