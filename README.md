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

# Copy my example config and customize for your setup  
cp configs/master-config.yaml.example configs/master-config.yaml

# Edit with your paths, MCP servers, agents, etc.
vim configs/master-config.yaml

# Initialize (creates symlinks, sets up sync)
./scripts/init.sh
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

1. Edit `configs/master-config.yaml` with your:
   - MCP server paths and commands
   - Agent library locations  
   - API keys (use environment variables)
   - Tool installation paths

2. Run `./scripts/init.sh` to set up symlinks and initial sync

3. Use `./scripts/sync.sh` whenever you change configs

## Sharing Your Setup

If you fork this:
- Keep your actual API keys in `.env` (gitignored)
- Share your `master-config.yaml` structure but not secrets
- Document any custom MCP servers or agents you've added
- Consider contributing back any useful sync scripts

## Why I Built This

Got tired of manually updating MCP configs across 4 different AI tools every time I added a new server. This keeps everything in sync from one master file.

Dotfiles philosophy: shareable structure, personal configuration.