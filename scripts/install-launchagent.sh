#!/bin/bash

# Install LaunchAgent for automatic Truffaldino sync
# This will watch for changes to Claude Desktop config and auto-sync

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LAUNCHAGENT_DIR="$HOME/Library/LaunchAgents"
PLIST_NAME="com.truffaldino.autosync"
PLIST_FILE="$LAUNCHAGENT_DIR/${PLIST_NAME}.plist"

echo "🤖 Installing Truffaldino LaunchAgent..."

# Create LaunchAgents directory if it doesn't exist
mkdir -p "$LAUNCHAGENT_DIR"

# Create the plist file
cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${PLIST_NAME}</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>${PROJECT_ROOT}/scripts/sync.sh</string>
    </array>
    
    <key>WatchPaths</key>
    <array>
        <string>\$HOME/Library/Application Support/Claude/claude_desktop_config.json</string>
        <string>${PROJECT_ROOT}/configs/master-config.yaml</string>
    </array>
    
    <key>RunAtLoad</key>
    <false/>
    
    <key>StandardOutPath</key>
    <string>${PROJECT_ROOT}/logs/autosync.log</string>
    
    <key>StandardErrorPath</key>
    <string>${PROJECT_ROOT}/logs/autosync.error.log</string>
    
    <key>EnvironmentVariables</key>
    <dict>
        <string>PATH</string>
        <string>/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin</string>
    </dict>
</dict>
</plist>
EOF

# Make sure logs directory exists
mkdir -p "$PROJECT_ROOT/logs"

# Load the LaunchAgent
echo "📂 Loading LaunchAgent..."
launchctl load "$PLIST_FILE"

# Enable the LaunchAgent
echo "✅ Enabling LaunchAgent..."
launchctl enable "gui/$(id -u)/${PLIST_NAME}"

echo "🎉 LaunchAgent installed successfully!"
echo ""
echo "The agent will automatically sync when:"
echo "  - Claude Desktop config changes"
echo "  - Your master-config.yaml changes"
echo ""
echo "Logs are written to:"
echo "  - ${PROJECT_ROOT}/logs/autosync.log"
echo "  - ${PROJECT_ROOT}/logs/autosync.error.log"
echo ""
echo "To check status: launchctl list | grep truffaldino"
echo "To uninstall: ./scripts/uninstall-launchagent.sh"