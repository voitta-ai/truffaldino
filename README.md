# Truffaldino - Personal AI Development Setup

My personal dotfiles-style configuration for managing AI agents, MCP servers, and development tools. Feel free to fork and adapt for your own setup.

## What This Is

This is my personal system for keeping AI development tools in sync across different environments. It's basically dotfiles for the AI era - handles configurations for Claude Desktop, Claude Code, Cline, JetBrains AI, MCP servers, and agent libraries.

Not a product, just sharing what works for me. Your mileage may vary.

## What It Does

- Keeps MCP server configs synced across all my AI tools
- Manages my personal agent library 
- Handles environment variables and API keys safely
- One command to sync everything when I add new tools

## My Setup

```bash
# Fork this, then clone to your preferred location
git clone https://github.com/yourusername/truffaldino.git ~/dotfiles/ai
cd ~/dotfiles/ai

# Install Python dependencies
pip3 install -r requirements.txt

# Smart import from all detected configs (recommended)
./scripts/smart-import.py

# OR simple import from Claude Desktop only
# ./scripts/import-from-claude.py

# OR manually copy example config and customize
# cp configs/master-config.yaml.example configs/master-config.yaml
# vim configs/master-config.yaml

# Set up environment variables
cp env/.env.template env/.env
vim env/.env  # Add your API keys

# Initialize the system
./scripts/init.sh

# Test sync
./scripts/sync.sh
```

## Directory Structure

```
truffaldino/
├── configs/          # My master config + tool-specific generation
├── sync/             # Scripts to keep everything in sync
├── agents/           # Symlinks to my agent libraries
├── env/              # Environment variable templates
└── scripts/          # Setup and maintenance scripts
```

## Personal Configuration

### Smart Import (Recommended)
1. **Smart detection**: `./scripts/smart-import.py`
   - Automatically detects Claude Desktop, Cline, JetBrains configs
   - Shows modification dates and conflict analysis
   - Creates intelligent superset with comments
   - Opens in $EDITOR for review before saving
   - Automatic versioning/backup of existing files

2. **Add your API keys**: Edit `env/.env` with actual values

3. **Initialize**: `./scripts/init.sh` sets up the system

4. **Sync**: `./scripts/sync.sh` syncs everything

### Manual Setup
If you prefer to start from scratch:

1. Copy example config: `cp configs/master-config.yaml.example configs/master-config.yaml`
2. Edit with your MCP servers, paths, etc.
3. Set up environment variables in `env/.env`
4. Run `./scripts/init.sh` and `./scripts/sync.sh`

## Sharing Your Setup

If you fork this:
- Keep your actual API keys in `.env` (gitignored)
- Share your `master-config.yaml` structure but not secrets
- Document any custom MCP servers or agents you've added
- Consider contributing back any useful sync scripts

## Automatic Sync (Optional)

Set up automatic syncing when configs change:

```bash
# Install LaunchAgent (macOS only)
./scripts/install-launchagent.sh

# Check if it's running
launchctl list | grep truffaldino

# View logs
tail -f logs/autosync.log

# Uninstall if needed
./scripts/uninstall-launchagent.sh
```

The LaunchAgent watches:
- Claude Desktop config changes
- Your master-config.yaml changes

When either changes, it automatically runs the sync.

## Configuration Management

### Smart Import (Multi-Tool Detection)
The smart import automatically detects and merges configs from multiple tools:

```bash
./scripts/smart-import.py
```

Features:
- **Auto-detection**: Finds Claude Desktop, Cline, JetBrains, Cursor, Windsurf configs  
- **Conflict analysis**: Shows where different tools have conflicting server configs
- **Superset creation**: Merges all unique servers with source attribution
- **Interactive editing**: Opens in $EDITOR with comments explaining conflicts
- **Version control**: Automatic backup of existing configs

### Simple Import (Single Tool)
For importing from specific tools:

```bash
# From Claude Desktop
./scripts/import-from-claude.py

# From Cline  
./scripts/import-from-claude.py --source cline

# From custom file
./scripts/import-from-claude.py --source file --file /path/to/config.json
```

### Version Management
RCS-style versioning for all configuration files:

```bash
# List all versions
./scripts/manage-versions.sh list

# List versions of specific file
./scripts/manage-versions.sh list master-config.yaml

# Show specific version
./scripts/manage-versions.sh show master-config.yaml 20240130_143022

# Compare versions
./scripts/manage-versions.sh diff master-config.yaml 20240130_143022 20240131_091445

# Restore to previous version
./scripts/manage-versions.sh restore master-config.yaml 20240130_143022

# Clean up old versions
./scripts/manage-versions.sh cleanup 30
```

## Why I Built This

Got tired of manually updating MCP configs across 4 different AI tools every time I added a new server. This keeps everything in sync from one master file.

Dotfiles philosophy: shareable structure, personal configuration.