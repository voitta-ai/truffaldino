# Truffaldino

**AI Development Configuration Manager**

Truffaldino synchronizes MCP (Model Context Protocol) servers and system prompts across multiple AI development tools. Think of it as "dotfiles for the AI era" - a simple way to keep your AI assistant configurations consistent across different applications.

## Supported Applications

| # | Application | MCP Support | Prompt Support | Status |
|---|-------------|-------------|----------------|---------|
| 1 | Claude Desktop | ✅ | ❌ | JSON config |
| 2 | Claude Code | ✅ | ❌ | CLI commands |
| 3 | Cline | ✅ | ✅ | JSON config |
| 4 | Cursor | ✅ | ✅ | JSON config |
| 5 | IntelliJ | ✅ | ✅ | XML config |

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository_url>
   cd truffaldino
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Make scripts executable:**
   ```bash
   chmod +x main.py mcp.py
   ```

## CLI Usage

### Command Line Flags

```bash
# List all supported AI applications
./main.py --list-apps

# Show MCP servers for a specific app (by number)
./main.py --show-mcps 1

# Show system prompt for a specific app
./main.py --show-prompt 3

# Sync MCP servers from one app to another
./main.py --sync-mcp --from 1 --to 3

# Sync prompts between apps
./main.py --sync-prompt --from 3 --to 4
```

### Interactive Mode

Run without arguments for an interactive menu:

```bash
./main.py
```

This will show:
```
🎪 Truffaldino - AI Development Configuration Manager

Available AI Applications:
1. ✅ Claude Desktop
2. ❌ Claude Code
3. ✅ Cline
4. ❌ Cursor
5. ✅ IntelliJ

Options:
a) List/Show MCP servers for an app
b) Sync MCP servers between apps
c) Show/Sync prompts between apps
d) Show system status
e) Exit

Choice: _
```

## MCP Server Usage

Truffaldino can be used as an MCP server to provide configuration management tools to AI assistants.

### Setup as MCP Server

1. **Add to your AI tool's configuration** (e.g., Claude Desktop):
   ```json
   {
     "mcpServers": {
       "truffaldino": {
         "command": "python",
         "args": ["/path/to/truffaldino/mcp.py"]
       }
     }
   }
   ```

2. **Restart your AI application** to load the new MCP server.

### Available MCP Tools

| Tool | Description |
|------|-------------|
| `truffaldino_list_apps` | List supported applications and installation status |
| `truffaldino_show_mcps` | Show MCP servers for a specific app |
| `truffaldino_sync_mcps` | Sync MCP servers between apps |
| `truffaldino_show_prompts` | Show system prompts for an app |
| `truffaldino_sync_prompts` | Sync prompts between apps |
| `truffaldino_status` | Show system status and health |
| `truffaldino_resolve_conflicts` | Handle configuration conflicts via file editing |

### Conflict Resolution

When conflicts are detected during sync operations in an MCP environment:

1. **Truffaldino creates a temporary conflict file** with details about conflicting configurations
2. **The AI assistant is instructed to have you edit the file** using your preferred editor (`$EDITOR`)
3. **You resolve conflicts** by uncommenting your preferred configuration for each server
4. **The AI assistant reloads** and applies your resolutions

Example conflict file:
```
# Truffaldino Configuration Conflicts
# Edit this file to resolve conflicts, then save and exit

## Server: filesystem
### Option 1 (Source):
# {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "/new/path"]}

### Option 2 (Target):  
# {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "/old/path"]}

### Your choice (uncomment one):
# KEEP: source
# KEEP: target
```

## Configuration Paths

### Claude Desktop
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/claude/config.json`
- **Windows**: `~/AppData/Roaming/Claude/config.json`

### Claude Code
- **All platforms**: Uses `claude mcp` CLI commands (no config file)

### Cline
- **All platforms**: `~/.cline/mcp_settings.json`
- **Prompts**: `~/.cline/system_prompt.txt`

### Cursor
- **All platforms**: `~/.cursor/mcp_config.json`
- **Prompts**: `~/.cursor/system_prompt.txt`

### IntelliJ
- **macOS**: `~/Library/Application Support/JetBrains/IntelliJIdea*/options/`
- **Linux**: `~/.config/JetBrains/IntelliJIdea*/options/`
- **Windows**: `~/AppData/Roaming/JetBrains/IntelliJIdea*/options/`
- **Config**: `llm.mcpServers.xml`
- **Prompts**: `ai_assistant_system_prompt.txt`

## Versioning System

Truffaldino automatically creates backups of configurations before making changes:

```
~/.truffaldino/
├── versions/
│   ├── claude_desktop_20250131_143022.json
│   ├── cline_20250131_143025.json
│   ├── cursor_20250131_143028.json
│   └── intellij_20250131_143030.xml
├── conflicts.log
└── config.json
```

- **Automatic backups** before every sync operation
- **Timestamped filenames** for easy identification
- **Keeps last 10 versions** per application
- **Restore functionality** (manual for now)

## Examples

See the `examples/` directory for sample configurations:

- `claude-desktop-config.json` - Claude Desktop MCP server setup
- `cline-config.json` - Cline/VS Code extension setup  
- `cursor-config.json` - Cursor IDE setup
- `intellij-config.xml` - IntelliJ XML configuration
- `base-prompt.md` - Example system prompt

## Architecture

### Core Files

- **`main.py`** - CLI entry point with argument parsing and interactive menu
- **`sync.py`** - Core synchronization logic and configuration management
- **`mcp.py`** - MCP server implementation
- **`config.py`** - Application definitions and configuration paths

### Key Classes

- **`AIApp`** - Represents an AI application with its configuration paths and capabilities
- **`ConfigManager`** - Handles loading/saving configurations across different formats (JSON/XML/CLI)
- **`SyncEngine`** - Core synchronization logic with conflict detection
- **`ConflictResolver`** - Handles configuration conflicts via temporary file editing

## Sync Modes

### Merge Mode (Default)
- Adds missing MCP servers from source to target
- Keeps existing servers in target unchanged
- Safe option that doesn't overwrite existing configurations

### Replace Mode
- Completely replaces target configuration with source
- Removes servers that exist only in target
- Use with caution as it's destructive

### Smart Mode (CLI only)
- Interactive conflict resolution
- Shows conflicting configurations side-by-side
- Lets you choose which configuration to keep for each conflict

## Troubleshooting

### Common Issues

1. **"App not found" errors**
   - Check if the application is installed
   - Verify configuration paths exist
   - For Claude Code, ensure `claude` CLI is in PATH

2. **Permission errors**
   - Ensure write permissions to configuration directories
   - Check if applications are running (may lock config files)

3. **MCP server not loading**
   - Verify Python path in configuration
   - Check that `mcp.py` is executable
   - Restart the AI application after adding MCP server

### Debug Information

Use the status command to check system health:
```bash
./main.py --list-apps  # Check which apps are detected
./main.py              # Interactive mode shows detailed status
```

Or via MCP:
```
Use the truffaldino_status tool to get system information
```

## Development

### Adding New AI Applications

1. **Update `config.py`** - Add new `AIApp` definition
2. **Extend `ConfigManager`** - Add loading/saving methods for the new format
3. **Update documentation** - Add paths and capabilities to README

### Contributing

- Follow existing code style and patterns
- Add error handling for new functionality
- Update documentation for any new features
- Test with multiple AI applications

## License

[Add your license here]

---

**Truffaldino** - Because managing AI configurations shouldn't be harder than using the AI itself. 🎪