#!/bin/bash
# Installation script for bare metal deployment
# Run as root or with sudo

set -e

APP_DIR="/opt/freshrss-mcp-server"
APP_USER="freshrss-mcp"
REPO_URL="https://github.com/your-username/freshrss-mcp-server.git"

echo "=== FreshRSS MCP Server Installation ==="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root or with sudo"
    exit 1
fi

# Create system user if it doesn't exist
if ! id "$APP_USER" &>/dev/null; then
    echo "Creating system user: $APP_USER"
    useradd -r -s /bin/false "$APP_USER"
fi

# Create application directory
echo "Creating application directory: $APP_DIR"
mkdir -p "$APP_DIR"

# Clone or update repository
if [ -d "$APP_DIR/.git" ]; then
    echo "Updating existing installation..."
    cd "$APP_DIR"
    git pull
else
    echo "Cloning repository..."
    git clone "$REPO_URL" "$APP_DIR"
    cd "$APP_DIR"
fi

# Install uv if not present
if ! command -v uv &>/dev/null; then
    echo "Installing uv..."
    pip install uv
fi

# Install Python dependencies
echo "Installing Python dependencies..."
cd "$APP_DIR"
uv sync --frozen --no-dev

# Install Playwright and browser
echo "Installing Playwright browser..."
uv run playwright install chromium
uv run playwright install-deps chromium

# Create .env file if it doesn't exist
if [ ! -f "$APP_DIR/.env" ]; then
    echo "Creating .env file template..."
    cat > "$APP_DIR/.env" << 'EOF'
# FreshRSS API Configuration (required)
FRESHRSS_API_URL=https://your-freshrss-instance/api/greader.php
FRESHRSS_USERNAME=your_username
FRESHRSS_API_PASSWORD=your_api_password

# MCP Server Configuration
MCP_TRANSPORT=streamable-http
MCP_HOST=0.0.0.0
MCP_PORT=8080

# Optional Settings
ENABLE_DYNAMIC_FETCH=true
LOG_LEVEL=INFO
EOF
    echo "Please edit $APP_DIR/.env with your FreshRSS credentials"
fi

# Set ownership
echo "Setting file ownership..."
chown -R "$APP_USER:$APP_USER" "$APP_DIR"

# Install systemd service
echo "Installing systemd service..."
cp "$APP_DIR/deploy/freshrss-mcp.service" /etc/systemd/system/
systemctl daemon-reload

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Next steps:"
echo "1. Edit $APP_DIR/.env with your FreshRSS credentials"
echo "2. Enable and start the service:"
echo "   sudo systemctl enable freshrss-mcp"
echo "   sudo systemctl start freshrss-mcp"
echo "3. Check status:"
echo "   sudo systemctl status freshrss-mcp"
echo "4. View logs:"
echo "   sudo journalctl -u freshrss-mcp -f"
echo ""
