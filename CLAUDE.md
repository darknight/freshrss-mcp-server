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

deploy/                    # Deployment configurations
├── freshrss-mcp.service   # Systemd service file
└── install.sh             # Bare metal installation script
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
MCP_TRANSPORT=sse           # "stdio", "sse", or "streamable-http"
MCP_HOST=0.0.0.0            # HTTP server host
MCP_PORT=8080               # HTTP server port

# Optional: Dynamic fetch / Playwright (defaults shown)
ENABLE_DYNAMIC_FETCH=true   # Enable Playwright for JS-rendered pages
BROWSER_TIMEOUT=30          # Playwright page load timeout in seconds

# Optional: Logging
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Optional: API Authentication (for public deployments)
API_KEY=                    # If set, requires Authorization: Bearer <key> header
```

## Running the Server

### Transport Modes

The server supports three transport modes:

| Mode | Use Case | Default |
|------|----------|---------|
| **SSE** | Remote/Self-hosted (legacy clients) | ✅ Default (0.0.0.0:8080) |
| **Streamable HTTP** | Remote/Self-hosted (modern clients) | Use `--transport streamable-http` |
| **STDIO** | Local (Claude Desktop) | Use `--transport stdio` |

### HTTP Mode (SSE/Streamable HTTP)

By default, the server starts in SSE mode for remote deployment:

```bash
# Install dependencies
uv sync

# Install Playwright browser (required for dynamic fetch)
uv run playwright install chromium

# Run with defaults (SSE on 0.0.0.0:8080)
uv run freshrss-mcp

# Or use streamable-http (recommended for new deployments)
uv run freshrss-mcp --transport streamable-http
```

Endpoints:
- **SSE mode**: `/sse` (MCP endpoint), `/health` (health check)
- **Streamable HTTP mode**: `/mcp` (MCP endpoint), `/health` (health check)

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
  --transport {stdio,sse,streamable-http}  Transport mode (default: sse)
  --host HOST              HTTP server host (default: 0.0.0.0)
  --port PORT              HTTP server port (default: 8080)
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

## Production Features

### Health Check Endpoint

Available at `/health` for SSE and Streamable HTTP modes:

```bash
curl http://localhost:8080/health
# {"status": "healthy", "version": "0.1.0", "transport": "streamable-http"}
```

Use for:
- Load balancer health checks
- Kubernetes liveness/readiness probes
- Monitoring systems

### API Authentication

For public deployments, enable simple API key authentication by setting `API_KEY`:

```bash
# Enable authentication
API_KEY=your-secret-key uv run freshrss-mcp --transport streamable-http

# Client requests must include header
curl -H "Authorization: Bearer your-secret-key" http://localhost:8080/mcp
```

**Note**: This is a simple API key authentication, not OAuth 2.1 compliant. For internal/personal use only. The `/health` endpoint does not require authentication.

### Graceful Shutdown

The server handles SIGTERM and SIGINT signals gracefully:
- Closes Playwright browser instances
- Cleans up resources before exit

This is important for container deployments and systemd services.

## Deployment

### Docker Deployment

Using Docker Compose (recommended):

```bash
# Create .env file with your credentials
cat > .env << EOF
FRESHRSS_API_URL=https://your-freshrss/api/greader.php
FRESHRSS_USERNAME=your_username
FRESHRSS_API_PASSWORD=your_password
EOF

# Start the service
docker compose up -d

# Check logs
docker compose logs -f
```

Or build and run manually:

```bash
docker build -t freshrss-mcp .
docker run -p 8080:8080 \
  -e FRESHRSS_API_URL=https://your-freshrss/api/greader.php \
  -e FRESHRSS_USERNAME=your_username \
  -e FRESHRSS_API_PASSWORD=your_password \
  -e API_KEY=your-secret-key \
  freshrss-mcp
```

The Docker image includes:
- Health check configuration
- Playwright browser pre-installed
- Streamable HTTP as default transport

### Bare Metal / VM Deployment

Use the provided installation script:

```bash
# Run as root
sudo ./deploy/install.sh

# Edit configuration
sudo nano /opt/freshrss-mcp-server/.env

# Start the service
sudo systemctl enable freshrss-mcp
sudo systemctl start freshrss-mcp

# Check status
sudo systemctl status freshrss-mcp
sudo journalctl -u freshrss-mcp -f
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
