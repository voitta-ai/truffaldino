#!/bin/bash

# Truffaldino Sync Script
# Main entry point for syncing all configurations

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🎪 Truffaldino Sync"

# Check dependencies
if ! command -v python3 &> /dev/null; then
    echo "❌ python3 is required but not installed"
    exit 1
fi

# Install Python dependencies if needed
if ! python3 -c "import yaml" 2>/dev/null; then
    echo "📦 Installing required Python packages..."
    pip3 install --user pyyaml
fi

# Load environment variables
if [ -f "$PROJECT_ROOT/env/.env" ]; then
    echo "🔑 Loading environment variables..."
    set -a
    source "$PROJECT_ROOT/env/.env"
    set +a
else
    echo "⚠️  No .env file found, some MCP servers may not work"
fi

# Run the sync manager
echo "🔄 Running sync manager..."
python3 "$PROJECT_ROOT/sync/sync-manager.py" "$@"

echo "🎉 Sync complete!"