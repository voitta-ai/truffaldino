#!/usr/bin/env python3
"""
Import existing Claude Desktop configuration to create master-config.yaml
This script reads from Claude Desktop config and creates the YAML source of truth
"""

import json
import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional
import argparse

def find_claude_desktop_config() -> Optional[Path]:
    """Find Claude Desktop config file"""
    possible_paths = [
        Path.home() / "Library/Application Support/Claude/claude_desktop_config.json",  # macOS
        Path.home() / ".config/claude/config.json",  # Linux
        Path.home() / "AppData/Roaming/Claude/config.json",  # Windows
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    return None

def find_cline_config() -> Optional[Path]:
    """Find Cline MCP config file"""
    cline_config = Path.home() / ".cline/mcp_settings.json"
    return cline_config if cline_config.exists() else None

def convert_claude_config_to_master(claude_config: Dict[str, Any]) -> Dict[str, Any]:
    """Convert Claude Desktop config format to master config format"""
    master_config = {
        "mcp_servers": {},
        "agents": {
            "source_directory": "/path/to/your/agents",
            "deployment_targets": {
                "claude_code": "~/.claude/agents"
            },
            "categories": [
                "engineering", "design", "marketing", "product", 
                "project-management", "studio-operations", "testing", "bonus"
            ]
        },
        "environment_variables": {
            "required": [],
            "optional": []
        },
        "tools": {
            "claude_desktop": {
                "config_path": "~/Library/Application Support/Claude/claude_desktop_config.json",
                "supports_env": True
            },
            "claude_code": {
                "config_command": "claude mcp",
                "supports_env": False
            }
        },
        "sync": {
            "auto_sync": True,
            "conflict_resolution": "prompt",
            "backup_on_sync": True
        }
    }
    
    # Convert MCP servers
    mcp_servers = claude_config.get("mcpServers", {})
    env_vars_found = set()
    
    for server_name, server_config in mcp_servers.items():
        master_server = {
            "command": server_config.get("command", ""),
            "args": server_config.get("args", []),
            "description": f"MCP server: {server_name}"
        }
        
        if "env" in server_config:
            master_server["env"] = server_config["env"]
            # Track environment variables we found
            for env_var in server_config["env"]:
                if env_var.startswith("${") and env_var.endswith("}"):
                    env_vars_found.add(env_var[2:-1])
                elif isinstance(server_config["env"][env_var], str) and server_config["env"][env_var].startswith("${"):
                    var_name = server_config["env"][env_var][2:-1]
                    env_vars_found.add(var_name)
                else:
                    env_vars_found.add(env_var)
        
        if "cwd" in server_config:
            master_server["cwd"] = server_config["cwd"]
            
        master_config["mcp_servers"][server_name] = master_server
    
    # Add found environment variables to the config
    master_config["environment_variables"]["required"] = sorted(list(env_vars_found))
    
    return master_config

def main():
    parser = argparse.ArgumentParser(description="Import existing config to create master-config.yaml")
    parser.add_argument("--source", choices=["claude", "cline", "file"], default="claude",
                       help="Source to import from")
    parser.add_argument("--file", type=str, help="Path to config file (when using --source file)")
    parser.add_argument("--output", type=str, help="Output path for master-config.yaml")
    args = parser.parse_args()
    
    # Find project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Determine source file
    source_file = None
    if args.source == "claude":
        source_file = find_claude_desktop_config()
        if not source_file:
            print("❌ Could not find Claude Desktop config file")
            print("   Expected locations:")
            print("   - ~/Library/Application Support/Claude/claude_desktop_config.json (macOS)")
            print("   - ~/.config/claude/config.json (Linux)")
            return 1
    elif args.source == "cline":
        source_file = find_cline_config()
        if not source_file:
            print("❌ Could not find Cline config file at ~/.cline/mcp_settings.json")
            return 1
    elif args.source == "file":
        if not args.file:
            print("❌ --file argument required when using --source file")
            return 1
        source_file = Path(args.file)
        if not source_file.exists():
            print(f"❌ File not found: {source_file}")
            return 1
    
    # Determine output file
    if args.output:
        output_file = Path(args.output)
    else:
        output_file = project_root / "configs" / "master-config.yaml"
    
    print(f"📖 Reading config from: {source_file}")
    
    # Read source config
    try:
        with open(source_file, 'r') as f:
            source_config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {source_file}: {e}")
        return 1
    except Exception as e:
        print(f"❌ Error reading {source_file}: {e}")
        return 1
    
    # Convert to master config format
    print("🔄 Converting to master config format...")
    master_config = convert_claude_config_to_master(source_config)
    
    # Write output
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Backup existing file if it exists
    if output_file.exists():
        backup_file = output_file.with_suffix('.yaml.bak')
        print(f"💾 Backing up existing config to: {backup_file}")
        output_file.rename(backup_file)
    
    print(f"📝 Writing master config to: {output_file}")
    with open(output_file, 'w') as f:
        yaml.dump(master_config, f, default_flow_style=False, indent=2, sort_keys=False)
    
    # Create .env template with found variables
    env_template_path = project_root / "env" / ".env.template"
    if master_config["environment_variables"]["required"]:
        print(f"🔑 Updating .env template with found environment variables...")
        env_content = "# Environment Variables (generated from import)\n"
        env_content += "# Fill in your actual values\n\n"
        
        for var in master_config["environment_variables"]["required"]:
            env_content += f"{var}=your_{var.lower()}_here\n"
        
        with open(env_template_path, 'w') as f:
            f.write(env_content)
    
    print("✅ Import complete!")
    print(f"📄 Master config created: {output_file}")
    
    if master_config["environment_variables"]["required"]:
        print(f"🔑 Environment template updated: {env_template_path}")
        print("   Next steps:")
        print("   1. Copy env/.env.template to env/.env")
        print("   2. Fill in your actual API keys in env/.env")
        print("   3. Run ./scripts/sync.sh to sync all configurations")
    else:
        print("   Next step: Run ./scripts/sync.sh to sync all configurations")
    
    return 0

if __name__ == "__main__":
    exit(main())