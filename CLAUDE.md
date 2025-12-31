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
- **Article Extraction**: trafilatura (static), Playwright (dynamic)
- **Browser Automation**: Playwright (for JS-rendered pages)
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
    ├── fetcher.py         # Full article fetcher (static + dynamic)
    └── browser.py         # Playwright browser wrapper

```

## MCP Tools

| Tool | Description |
|------|-------------|
| `get_unread_articles` | Fetch unread articles list |
| `get_article_content` | Get single article content |
| `fetch_full_article` | Scrape full content from original URL (supports `force_dynamic` for JS sites) |
| `mark_as_read` | Mark articles as read |
| `get_subscriptions` | Get subscription feeds list |

## Environment Variables

```bash
# Required: FreshRSS API
FRESHRSS_API_URL=https://your-freshrss-instance/api/greader.php
FRESHRSS_USERNAME=your_username
FRESHRSS_API_PASSWORD=your_api_password

# Optional: MCP Server (defaults shown)
MCP_TRANSPORT=sse      # "stdio" or "sse"
MCP_HOST=0.0.0.0       # HTTP server host
MCP_PORT=8080          # HTTP server port

# Optional: Dynamic fetch / Playwright (defaults shown)
ENABLE_DYNAMIC_FETCH=true   # Enable Playwright for JS-rendered pages
BROWSER_TIMEOUT=30          # Playwright page load timeout in seconds
```

## Running the Server

### Transport Modes

The server supports two transport modes:

| Mode | Use Case | Default |
|------|----------|---------|
| **SSE** | Remote/Self-hosted | ✅ Default (0.0.0.0:8080) |
| **STDIO** | Local (Claude Desktop) | Use `--transport stdio` |

### SSE/HTTP Mode (Default)

By default, the server starts in SSE mode for remote deployment:

```bash
# Install dependencies
uv sync

# Install Playwright browser (required for dynamic fetch)
uv run playwright install chromium

# Run with defaults (SSE on 0.0.0.0:8080)
uv run freshrss-mcp

# Or configure via environment variables
MCP_TRANSPORT=sse MCP_HOST=0.0.0.0 MCP_PORT=8080 uv run freshrss-mcp
```

SSE endpoints:
- SSE: `http://<host>:<port>/sse`
- Messages: `http://<host>:<port>/messages/`

### STDIO Mode (Claude Desktop)

For local use with Claude Desktop:

```bash
# Override via CLI
uv run freshrss-mcp --transport stdio

# Or via environment variable
MCP_TRANSPORT=stdio uv run freshrss-mcp
```

### CLI Options

CLI arguments override environment variables:

```bash
uv run freshrss-mcp --help

Options:
  --transport {stdio,sse}  Transport mode (env: MCP_TRANSPORT, default: sse)
  --host HOST              HTTP server host (env: MCP_HOST, default: 0.0.0.0)
  --port PORT              HTTP server port (env: MCP_PORT, default: 8080)
  --version                Show version
```

### MCP Client Configuration (Claude Desktop)

```json
{
  "mcpServers": {
    "freshrss": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/freshrss-mcp-server", "freshrss-mcp", "--transport", "stdio"],
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

### MCP Inspector (Local Debugging)

Use the MCP Inspector web UI to interactively test and debug the server:

```bash
npx @modelcontextprotocol/inspector uv run python -m freshrss_mcp_server.server
```

This opens a browser interface where you can:
- View available tools and their schemas
- Execute tools with custom parameters
- Inspect request/response payloads

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
   - If content appears incomplete (JS placeholders), retry with `force_dynamic=True`
4. AI generates summary report for all articles
5. After user reads, AI calls `mark_as_read` to mark as read

## Docker Deployment

Use Microsoft's official Playwright image for easy deployment:

```dockerfile
FROM mcr.microsoft.com/playwright/python:v1.57.0-noble

WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY src/ ./src/

RUN pip install uv && uv sync

# Browser already installed in base image

ENV ENABLE_DYNAMIC_FETCH=true

CMD ["uv", "run", "freshrss-mcp"]
```

Build and run:

```bash
docker build -t freshrss-mcp .
docker run -p 8080:8080 \
  -e FRESHRSS_API_URL=https://your-freshrss/api/greader.php \
  -e FRESHRSS_USERNAME=your_username \
  -e FRESHRSS_API_PASSWORD=your_password \
  freshrss-mcp
```
