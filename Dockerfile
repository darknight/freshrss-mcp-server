# Use Microsoft's official Playwright image with pre-installed browsers
FROM mcr.microsoft.com/playwright/python:v1.57.0-noble

WORKDIR /app

# Copy dependency files first for better caching
# Use uv.lock* to handle case where file doesn't exist
COPY pyproject.toml ./
COPY uv.lock* ./

# Install uv and project dependencies
RUN pip install uv && uv sync --frozen --no-dev

# Copy source code
COPY src/ ./src/

# Browser is already installed in the base image, no need to run playwright install

# Default environment variables
ENV ENABLE_DYNAMIC_FETCH=true
ENV MCP_TRANSPORT=streamable-http
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8080
ENV LOG_LEVEL=INFO

# Health check - requires curl which is available in the base image
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

EXPOSE 8080

CMD ["uv", "run", "freshrss-mcp"]
