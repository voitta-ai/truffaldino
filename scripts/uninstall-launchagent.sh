#!/bin/bash

# Uninstall Truffaldino LaunchAgent

set -e

LAUNCHAGENT_DIR="$HOME/Library/LaunchAgents"
PLIST_NAME="com.truffaldino.autosync"
PLIST_FILE="$LAUNCHAGENT_DIR/${PLIST_NAME}.plist"

echo "🗑️  Uninstalling Truffaldino LaunchAgent..."

# Check if the plist file exists
if [ ! -f "$PLIST_FILE" ]; then
    echo "❌ LaunchAgent not found at: $PLIST_FILE"
    exit 1
fi

# Disable the LaunchAgent
echo "⏹️  Disabling LaunchAgent..."
launchctl disable "gui/$(id -u)/${PLIST_NAME}" || true

# Unload the LaunchAgent
echo "📤 Unloading LaunchAgent..."
launchctl unload "$PLIST_FILE" || true

# Remove the plist file
echo "🗑️  Removing plist file..."
rm "$PLIST_FILE"

echo "✅ LaunchAgent uninstalled successfully!"
echo ""
echo "Note: Log files are preserved in logs/ directory"