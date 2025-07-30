# Truffaldino - Personal AI Development Setup

My personal dotfiles-style configuration for managing AI agents, MCP servers, and development tools. Feel free to fork and adapt for your own setup.

## What This Is

This is my personal system for keeping AI development tools in sync across different environments. It's basically dotfiles for the AI era - handles configurations for Claude Desktop, Claude Code, Cline, JetBrains AI, MCP servers, and agent libraries.

Not a product, just sharing what works for me. Your mileage may vary.

## What It Does

- Keeps MCP server configs synced across all my AI tools
- Manages my personal agent library 
- Handles environment variables and API keys safely
- Syncs base system prompts across all AI assistants
- One command to sync everything when I add new tools
- Provides MCP server so any AI assistant can manage the system

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
vim env/.env  # Add your API keys and base prompt path

# Set up base prompt (optional)
cp prompts/base-prompt.md.example prompts/base-prompt.md
vim prompts/base-prompt.md  # Customize your base prompt

# Initialize the system
./scripts/init.sh

# Test sync
./scripts/sync.sh

# Build and test MCP server
cd mcp-server && npm install && npm run build
```

## Directory Structure

```
truffaldino/
├── configs/          # Master config + tool-specific generation
├── sync/             # Configuration sync tools
├── agents/           # Agent library management
├── env/              # Environment variable templates
├── prompts/          # Base prompt templates
├── scripts/          # All management scripts
├── mcp-server/       # Truffaldino MCP server
└── versions/         # Automatic backups (in ~/.truffaldino/)
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
3. Set up environment variables in `env/.env` (including BASE_PROMPT path)
4. Set up base prompt: `cp prompts/base-prompt.md.example prompts/base-prompt.md`
5. Run `./scripts/init.sh` and `./scripts/sync.sh`

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

### Prompt Management
Sync your base prompt across all AI tools:

```bash
# Sync base prompt to all detected AI tools
./scripts/sync-prompts.py

# Sync to specific tools only
./scripts/sync-prompts.py --tools claude_code cline cursor

# Dry run (show what would be done)
./scripts/sync-prompts.py --dry-run

# List available tools
./scripts/sync-prompts.py --list
```

### Master Management Tool
Unified interface for all Truffaldino operations:

```bash
# Show system status
./scripts/truffaldino.py status

# Interactive mode
./scripts/truffaldino.py --interactive

# Run any command through the master tool
./scripts/truffaldino.py sync
./scripts/truffaldino.py import
./scripts/truffaldino.py sync-prompts
```

### MCP Server Integration
The Truffaldino MCP server lets any AI assistant manage your configuration:

```bash
# Build the MCP server
cd mcp-server
npm install
npm run build

# Add to your master-config.yaml:
# truffaldino:
#   command: node
#   args: ["mcp-server/dist/index.js"]
#   cwd: "/path/to/your/truffaldino"
#   description: "Truffaldino configuration management"

# Then sync to make it available to all AI tools
./scripts/sync.sh
```

Available MCP tools:
- `truffaldino_status` - Show system status
- `truffaldino_sync` - Sync all configurations  
- `truffaldino_import` - Smart import from detected tools
- `truffaldino_sync_prompts` - Sync base prompt to all tools
- `truffaldino_list_versions` - List configuration backups
- `truffaldino_restore_version` - Restore previous version
- `truffaldino_install_automation` - Set up auto-sync
- `truffaldino_help` - Show detailed help

## Why I Built This

Got tired of manually updating MCP configs across 4 different AI tools every time I added a new server. This keeps everything in sync from one master file.

Dotfiles philosophy: shareable structure, personal configuration.