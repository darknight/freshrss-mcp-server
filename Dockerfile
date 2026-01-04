# Use Microsoft's official Playwright image with pre-installed browsers
FROM mcr.microsoft.com/playwright/python:v1.57.0-noble

WORKDIR /app

# Copy dependency files first for better caching
# Use uv.lock* to handle case where file doesn't exist
COPY pyproject.toml ./
COPY uv.lock* ./
COPY README.md ./

# Install uv and project dependencies
RUN pip install uv && uv sync --frozen --no-dev

# Copy source code
COPY src/ ./src/

# Browser is already installed in the base image, no need to run playwright install

# Default environment variables
ENV ENABLE_DYNAMIC_FETCH=true
ENV MCP_TRANSPORT=streamable-http
ENV MCP_HOST=::
ENV LOG_LEVEL=INFO
# Note: MCP_PORT defaults to 8080, but Railway will inject PORT which is auto-detected

# Health check - uses PORT env var with fallback to 8080
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

EXPOSE 8080

CMD ["uv", "run", "freshrss-mcp"]
