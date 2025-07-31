#!/bin/bash

# Truffaldino Setup Script
# Sets up symlinks and initial configuration

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🎪 Initializing Truffaldino..."

# No master config needed anymore - we sync directly between tools
echo "ℹ️  Truffaldino now uses direct JSON syncing between AI tools"
echo "   No master config file needed!"

# Check if .env exists
if [ ! -f "$PROJECT_ROOT/env/.env" ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp "$PROJECT_ROOT/env/.env.template" "$PROJECT_ROOT/env/.env"
    echo "   Please edit env/.env with your API keys"
fi

# Create directories
mkdir -p "$PROJECT_ROOT/configs/generated"
mkdir -p "$PROJECT_ROOT/backups"
mkdir -p "$PROJECT_ROOT/logs"

# Make scripts executable
chmod +x "$PROJECT_ROOT/scripts"/*.sh

# Create symlink to the sync script in your PATH (optional)
if [ -d "$HOME/.local/bin" ]; then
    ln -sf "$PROJECT_ROOT/scripts/sync.sh" "$HOME/.local/bin/truffaldino-sync"
    echo "✅ Created truffaldino-sync command in ~/.local/bin"
fi

echo "✅ Truffaldino initialized!"
echo ""
echo "Next steps:"
echo "1. Run ./scripts/sync.sh to sync configs between AI tools"
echo "   OR ./scripts/smart-import.py to create a superset from all tools"
echo "2. Edit env/.env with your API keys and BASE_PROMPT path"
echo "3. Build MCP server: cd mcp-server && npm install && npm run build"
echo "4. Optionally install LaunchAgent: ./scripts/install-launchagent.sh"
echo "5. View version history: ./scripts/manage-versions.sh list"