#!/bin/bash

# Truffaldino Sync Script
# Interactive JSON-based configuration sync

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
if ! python3 -c "import dotenv" 2>/dev/null; then
    echo "📦 Installing required Python packages..."
    if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
        pip3 install --user -r "$PROJECT_ROOT/requirements.txt"
    else
        pip3 install --user python-dotenv
    fi
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

# Run the new sync manager
echo "🔄 Starting interactive sync..."
python3 "$PROJECT_ROOT/sync/sync-manager-v2.py" "$@"

echo "🎉 Sync complete!"