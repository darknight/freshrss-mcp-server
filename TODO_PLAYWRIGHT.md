# TODO: Playwright Dynamic Content Rendering

## Overview

Add support for extracting content from JavaScript-rendered pages using Playwright.

## Problem

Currently, `trafilatura` only processes static HTML. Pages that require JavaScript execution to render content (SPAs, dynamic loading) return incomplete or empty content.

## Proposed Solution

Add an optional Playwright-based fetcher as a fallback or alternative to the current `trafilatura` approach.

## Implementation Plan

### 1. Add Dependencies

```toml
# pyproject.toml - optional dependency group
[project.optional-dependencies]
playwright = ["playwright>=1.40.0"]
```

### 2. Create Playwright Fetcher Module

**File**: `src/freshrss_mcp_server/tools/playwright_fetcher.py`

```python
async def fetch_with_playwright(url: str, timeout: int = 30) -> dict:
    """Fetch article content using headless browser.

    Args:
        url: Article URL to fetch
        timeout: Page load timeout in seconds

    Returns:
        Extracted content with title and text
    """
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle", timeout=timeout * 1000)

        # Get rendered HTML
        html = await page.content()

        await browser.close()

    # Extract content from rendered HTML using trafilatura
    content = trafilatura.extract(html)
    return {"url": url, "content": content}
```

### 3. Update fetch_full_article Tool

Add parameter to choose rendering mode:

```python
@server.tool()
async def fetch_full_article(
    url: str,
    use_browser: bool = False,  # New parameter
) -> dict:
    """Fetch full article content from original URL.

    Args:
        url: Article URL to fetch
        use_browser: If True, use Playwright for JS-rendered pages

    Returns:
        Extracted article content
    """
    if use_browser:
        return await playwright_fetcher.fetch_with_playwright(url)
    else:
        return await fetcher.fetch_full_article(url)
```

### 4. Installation Notes

Users need to install Playwright browsers:

```bash
# Install with playwright support
uv sync --extra playwright

# Install browsers
uv run playwright install chromium
```

## Considerations

1. **Dependency Size**: Playwright + Chromium is ~200MB+
2. **Performance**: Browser rendering is slower than static parsing
3. **Resource Usage**: More CPU/memory for headless browser
4. **Optional**: Should be an optional feature, not required

## Alternatives Considered

| Option | Pros | Cons |
|--------|------|------|
| Playwright | Full JS support, reliable | Large dependency, resource heavy |
| Selenium | Mature, well-documented | Requires external driver |
| requests-html | Lightweight | Limited JS support |
| Pyppeteer | Chromium-based | Less maintained |

**Recommendation**: Playwright - best balance of features and maintenance.

## Priority

Low - Most RSS feeds provide full content or usable summaries. This is only needed for specific sites that heavily rely on JavaScript rendering.
