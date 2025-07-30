#!/bin/bash

# Truffaldino Setup Script
# Sets up symlinks and initial configuration

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🎪 Initializing Truffaldino..."

# Check if master config exists
if [ ! -f "$PROJECT_ROOT/configs/master-config.yaml" ]; then
    echo "❌ No master-config.yaml found. Please copy and customize the example:"
    echo "   cp configs/master-config.yaml.example configs/master-config.yaml"
    echo "   vim configs/master-config.yaml"
    exit 1
fi

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
echo "1. Import configs: ./scripts/smart-import.py (detects all tools)"
echo "   OR ./scripts/import-from-claude.py (Claude Desktop only)"
echo "   OR edit configs/master-config.yaml manually"
echo "2. Edit env/.env with your API keys"
echo "3. Run ./scripts/sync.sh to sync all configurations"
echo "4. Optionally install LaunchAgent: ./scripts/install-launchagent.sh"
echo "5. View version history: ./scripts/manage-versions.sh list"