# Use Microsoft's official Playwright image with pre-installed browsers
FROM mcr.microsoft.com/playwright/python:v1.57.0-noble

WORKDIR /app

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock ./

# Install uv and project dependencies
RUN pip install uv && uv sync --frozen

# Copy source code
COPY src/ ./src/

# Browser is already installed in the base image, no need to run playwright install

# Default environment variables
ENV ENABLE_DYNAMIC_FETCH=true
ENV MCP_TRANSPORT=sse
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8080

EXPOSE 8080

CMD ["uv", "run", "freshrss-mcp"]
