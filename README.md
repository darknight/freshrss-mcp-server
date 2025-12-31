# FreshRSS MCP Server

An MCP (Model Context Protocol) server that connects to a self-hosted FreshRSS instance, enabling AI applications to fetch and manage RSS subscription articles.

## Features

- **Fetch Unread Articles**: Get all unread articles from your RSS subscriptions
- **Article Content**: Access full article content with title, summary, link, and publication date
- **Full Article Scraping**: Extract complete article text from original URLs (for summary-only feeds)
- **Mark as Read**: Mark articles as read after processing
- **Subscription Management**: View all subscriptions with unread counts

## Installation

### Prerequisites

- Python 3.14+
- [UV](https://docs.astral.sh/uv/) package manager
- A self-hosted [FreshRSS](https://freshrss.org/) instance with API enabled

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/freshrss-mcp-server.git
cd freshrss-mcp-server
```

2. Install dependencies:
```bash
uv sync
```

3. Create `.env` file with your FreshRSS credentials:
```bash
cp .env.example .env
# Edit .env with your credentials
```

## Configuration

Create a `.env` file with the following variables:

```bash
# Required: FreshRSS API
FRESHRSS_API_URL=https://your-freshrss-instance/api/greader.php
FRESHRSS_USERNAME=your_username
FRESHRSS_API_PASSWORD=your_api_password

# Optional: Request settings
REQUEST_TIMEOUT=30
DEFAULT_ARTICLE_LIMIT=100

# Optional: MCP Server (defaults shown)
MCP_TRANSPORT=sse      # "stdio" or "sse"
MCP_HOST=0.0.0.0       # HTTP server host
MCP_PORT=8080          # HTTP server port
```

### FreshRSS API Setup

1. In FreshRSS, go to Settings > Profile
2. Enable "Allow API access"
3. Set an API password (different from your login password)
4. Use this API password in your `.env` file

## Usage

### Running the Server

**SSE/HTTP Mode** (default, for remote deployment):
```bash
# Run with defaults (SSE on 0.0.0.0:8080)
uv run freshrss-mcp
```

**STDIO Mode** (for Claude Desktop):
```bash
uv run freshrss-mcp --transport stdio
```

**CLI Options** (override environment variables):
```
--transport {stdio,sse}  Transport mode (env: MCP_TRANSPORT, default: sse)
--host HOST              HTTP server host (env: MCP_HOST, default: 0.0.0.0)
--port PORT              HTTP server port (env: MCP_PORT, default: 8080)
--version                Show version
```

### Claude Desktop Configuration

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

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

## Available Tools

### `get_unread_articles`
Fetch unread articles from FreshRSS.

**Parameters:**
- `limit` (optional, default: 100): Maximum number of articles to return
- `feed_id` (optional): Filter by specific feed ID

**Returns:** List of articles with id, title, summary, link, published, feed_title

### `get_article_content`
Get full content of a specific article.

**Parameters:**
- `article_id`: The article ID to fetch

**Returns:** Article with full content

### `mark_as_read`
Mark articles as read.

**Parameters:**
- `article_ids`: List of article IDs to mark as read

**Returns:** Operation result with success status

### `get_subscriptions`
Get all RSS feed subscriptions with unread counts.

**Returns:** List of subscriptions with id, title, url, unread_count, category

### `fetch_full_article`
Fetch full article content from original URL (for summary-only feeds).

**Parameters:**
- `url`: The original article URL to fetch

**Returns:** Extracted article content with title and text

## Example Workflow

1. AI calls `get_unread_articles` to fetch unread article list
2. AI analyzes titles and summaries to determine importance
3. For incomplete summaries, AI calls `fetch_full_article` to get full content
4. AI generates summary report for all articles
5. After user reviews, AI calls `mark_as_read` to mark articles as read

## Development

### MCP Inspector (Local Debugging)

Use the MCP Inspector web UI to interactively test and debug the server:

```bash
npx @modelcontextprotocol/inspector uv run python -m freshrss_mcp_server.server
```

This opens a browser interface where you can view available tools, execute them with custom parameters, and inspect request/response payloads.

### Running Tests

```bash
# Quick API test
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

asyncio.run(test())
"
```

### Linting & Type Checking

```bash
# Format code
ruff format .

# Check for issues
ruff check .

# Type check
uv run ty check .
```

## Tech Stack

- **Python 3.14**
- **UV** - Package manager
- **Ruff** - Linter/Formatter
- **ty** - Type checker
- **MCP SDK** - Model Context Protocol
- **httpx** - Async HTTP client
- **Pydantic** - Data validation
- **trafilatura** - Article content extraction

## License

MIT License - see [LICENSE](LICENSE) for details.
