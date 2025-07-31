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

# Set up environment variables
cp env/.env.template env/.env
vim env/.env  # Add your API keys and base prompt path

# Set up base prompt (optional)
cp prompts/base-prompt.md.example prompts/base-prompt.md
vim prompts/base-prompt.md  # Customize your base prompt

# Initialize the system
./scripts/init.sh

# Interactive sync between AI tools
./scripts/sync.sh
# This will:
# 1. Detect all your AI tool configs (Claude, Cline, etc.)
# 2. Let you choose which tool to sync FROM
# 3. Let you choose which tools to sync TO
# 4. Handle conflicts intelligently

# Build MCP server (optional - lets AI assistants manage Truffaldino)
cd mcp-server && npm install && npm run build
```

## Directory Structure

```
truffaldino/
├── configs/          # Config examples and generated files
├── sync/             # Configuration sync tools
├── agents/           # Agent library management  
├── env/              # Environment variable templates
├── prompts/          # Base prompt templates
├── scripts/          # All management scripts
├── mcp-server/       # Truffaldino MCP server
└── ~/.truffaldino/   # Version backups (in home directory)
```

## How It Works

### Interactive Sync (Primary Workflow)
The main workflow is now interactive JSON-based syncing:

```bash
./scripts/sync.sh
```

This will:
1. **Detect all AI tool configs** on your system (Claude Desktop, Cline, etc.)
2. **Show what's available** with file paths and status
3. **Let you choose source** - which config to sync FROM
4. **Let you choose targets** - which configs to sync TO
5. **Handle conflicts** - merge, replace, or review each conflict
6. **Backup automatically** - versions saved before any changes

Example session:
```
📂 Detected configurations:
1. ✅ Claude Desktop    ~/Library/Application Support/Claude/claude_desktop_config.json
2. ✅ Cline            ~/.cline/mcp_settings.json
3. ➕ Cursor           ~/.cursor/mcp_config.json

📤 Select source configuration:
1. Claude Desktop
2. Cline
Source (number): 1

✅ Loaded 5 MCP servers from Claude Desktop

📥 Select target configurations (comma-separated numbers, or 'all'):
2. Cline            (exists)
3. Cursor           (will create)
Targets: all

🔄 Select sync mode:
1. Merge - Add missing servers only
2. Replace - Replace all servers
3. Smart - Merge with conflict resolution
Mode (1-3): 3
```

### Smart Import (Alternative)
For creating a superset from ALL detected configs:

```bash
./scripts/smart-import.py
```

This creates a merged config with conflict annotations that you can edit.

## Sharing Your Setup

If you fork this:
- Keep your actual API keys in `.env` (gitignored)
- The system works with YOUR existing configs - no master file needed
- Document any custom MCP servers in configs/claude-desktop-example.json
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

### Direct Tool-to-Tool Sync (Primary Method)
No master config needed! Sync directly between your AI tools:

```bash
./scripts/sync.sh
```

The interactive workflow lets you:
- Choose any detected tool as the source
- Sync to one or multiple target tools  
- Handle conflicts with merge/replace/smart modes
- Automatically backup before changes

### Import from All Tools (Alternative)
Create a superset config from ALL your tools:

```bash
./scripts/smart-import.py
```

This:
- Detects all AI tool configs
- Shows conflicts between different tools
- Creates annotated JSON you can edit
- Saves to `configs/truffaldino.json`

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

#### Step 1: Build the MCP Server
```bash
# Build the MCP server
cd mcp-server
npm install
npm run build
cd ..
```

#### Step 2: Add to Your Configuration
Add the Truffaldino MCP server to any AI tool config (e.g., Claude Desktop):

```json
{
  "mcpServers": {
    "truffaldino": {
      "command": "node",
      "args": ["mcp-server/dist/index.js"],
      "cwd": "/Users/yourusername/path/to/truffaldino"
    }
  }
}
```

**IMPORTANT**: The `cwd` must be the full absolute path to your Truffaldino directory.

#### Step 3: Sync to Other Tools
```bash
# Use the interactive sync to propagate to other tools
./scripts/sync.sh
# Choose the tool you edited as source
# Choose other tools as targets
```

#### Step 4: Restart Claude Desktop
After syncing, **you must restart Claude Desktop** for the MCP server to be available:
- Quit Claude Desktop completely (Cmd+Q on macOS)
- Start Claude Desktop again
- The Truffaldino tools will now be available

#### Step 5: Test in Claude
You can now ask Claude to use Truffaldino tools:
- "Show me the Truffaldino system status"
- "Sync all my configurations" 
- "Import configs from all my AI tools"
- "Sync my base prompt to all assistants"

#### Available MCP Tools
Once configured, these tools are available to any AI assistant:
- `truffaldino_status` - Show system status and health
- `truffaldino_sync` - Sync all configurations  
- `truffaldino_import` - Smart import from detected tools
- `truffaldino_sync_prompts` - Sync base prompt to all tools
- `truffaldino_list_versions` - List configuration backups
- `truffaldino_restore_version` - Restore previous version
- `truffaldino_install_automation` - Set up auto-sync (macOS)
- `truffaldino_help` - Show detailed help

#### Troubleshooting MCP Server
If the tools aren't working:

1. **Check the server is in your config**:
   ```bash
   cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | grep truffaldino
   ```

2. **Verify the path is correct**:
   - Must be an absolute path (starts with `/`)
   - The path must point to your Truffaldino directory
   - Example: `/Users/jane/projects/truffaldino`

3. **Check server logs**:
   - Claude Desktop logs: `~/Library/Logs/Claude/`
   - Look for any error messages about the Truffaldino server

4. **Test the server manually**:
   ```bash
   cd /path/to/truffaldino
   node mcp-server/dist/index.js
   # Should output: "Truffaldino MCP server running on stdio"
   ```

## Why I Built This

Got tired of manually updating MCP configs across 4 different AI tools every time I added a new server. This keeps everything in sync from one master file.

Dotfiles philosophy: shareable structure, personal configuration.