# FreshRSS MCP Server

## Project Overview

An MCP (Model Context Protocol) Server that connects to a self-hosted FreshRSS instance, enabling AI applications to fetch RSS subscription articles for intelligent summarization.

## Tech Stack

- **Language**: Python 3.14
- **Package Manager**: UV
- **Linter/Formatter**: Ruff (installed via `uv tool install ruff@latest`)
- **Type Checker**: ty (dev dependency)
- **MCP SDK**: mcp-python-sdk (mcp[cli] >= 1.25.0)
- **HTTP Client**: httpx (async)
- **Data Validation**: Pydantic + pydantic-settings
- **Article Extraction**: trafilatura
- **API**: FreshRSS Google Reader compatible API

## Core Features

1. **Fetch Unread Articles**: Get all unread articles from FreshRSS
2. **Article Content**: Return title, summary/content, original link, publish time, feed info
3. **Full Article Scraping**: Scrape full content for summary-only RSS feeds
4. **Mark as Read**: Mark articles as read

## Project Structure

```
src/freshrss_mcp_server/
├── __init__.py            # Package exports
├── server.py              # MCP Server entry point
├── config.py              # Settings management
├── exceptions.py          # Custom exceptions
├── api/
│   ├── __init__.py
│   ├── client.py          # FreshRSS API client
│   └── models.py          # Pydantic data models
└── tools/
    ├── __init__.py
    ├── articles.py        # Article-related tools
    └── fetcher.py         # Full article fetcher

```

## MCP Tools

| Tool | Description |
|------|-------------|
| `get_unread_articles` | Fetch unread articles list |
| `get_article_content` | Get single article content |
| `fetch_full_article` | Scrape full content from original URL |
| `mark_as_read` | Mark articles as read |
| `get_subscriptions` | Get subscription feeds list |

## Environment Variables

```bash
FRESHRSS_API_URL=https://your-freshrss-instance/api/greader.php
FRESHRSS_USERNAME=your_username
FRESHRSS_API_PASSWORD=your_api_password
```

## Running the Server

### Development

```bash
# Install dependencies
uv sync

# Run MCP Server (stdio mode)
uv run python -m freshrss_mcp_server.server
```

### MCP Client Configuration (Claude Desktop)

```json
{
  "mcpServers": {
    "freshrss": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/freshrss-mcp-server", "python", "-m", "freshrss_mcp_server.server"],
      "env": {
        "FRESHRSS_API_URL": "https://your-freshrss-instance/api/greader.php",
        "FRESHRSS_USERNAME": "your_username",
        "FRESHRSS_API_PASSWORD": "your_api_password"
      }
    }
  }
}
```

## Development Commands

**IMPORTANT**: Run these commands after every code change.

### Linting & Formatting (Ruff)

```bash
# Check for linting issues
ruff check .

# Auto-fix linting issues
ruff check --fix .

# Format code
ruff format .

# Check formatting without changes
ruff format --check .
```

### Type Checking (ty)

```bash
# Type check the project
uv run ty check .

# Type check specific directory
uv run ty check src/
```

### All-in-One (run after code changes)

```bash
ruff format . && ruff check --fix . && uv run ty check .
```

### Quick API Test

```bash
uv run python -c "
import asyncio
from freshrss_mcp_server.api.client import FreshRSSClient
from freshrss_mcp_server.config import get_settings

async def test():
    settings = get_settings()
    async with FreshRSSClient(
        settings.freshrss_api_url,
        settings.freshrss_username,
        settings.freshrss_api_password,
    ) as client:
        subs = await client.get_subscriptions()
        print(f'Found {len(subs)} subscriptions')
        articles = await client.get_unread_articles(limit=5)
        print(f'Found {len(articles)} unread articles')

asyncio.run(test())
"
```

## FreshRSS API Reference

API Source: https://github.com/FreshRSS/FreshRSS/blob/edge/p/api/greader.php

### Key Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/accounts/ClientLogin` | Login, get Auth token |
| `/reader/api/0/subscription/list` | Get subscription list |
| `/reader/api/0/stream/contents/...` | Get article content |
| `/reader/api/0/unread-count` | Get unread counts |
| `/reader/api/0/edit-tag` | Mark read/starred |

## Usage Flow

1. AI calls `get_unread_articles` to fetch unread article list
2. AI analyzes titles and summaries to determine importance
3. For incomplete summaries, AI calls `fetch_full_article` to get full content
4. AI generates summary report for all articles
5. After user reads, AI calls `mark_as_read` to mark as read
