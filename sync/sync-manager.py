#!/usr/bin/env python3
"""
Truffaldino Sync Manager
Reads master config and generates tool-specific configurations
"""

import os
import json
import yaml
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
import argparse
from dotenv import load_dotenv

class SyncManager:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.config_dir = project_root / "configs"
        self.generated_dir = self.config_dir / "generated"
        self.master_config_path = self.config_dir / "master-config.yaml"
        
        # Ensure directories exist
        self.generated_dir.mkdir(exist_ok=True)
        
    def load_master_config(self) -> Dict[str, Any]:
        """Load the master configuration file"""
        if not self.master_config_path.exists():
            raise FileNotFoundError(f"Master config not found: {self.master_config_path}")
            
        with open(self.master_config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        # Expand environment variables
        self._expand_env_vars(config)
        return config
    
    def _expand_env_vars(self, obj: Any) -> None:
        """Recursively expand environment variables in config"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                    env_var = value[2:-1]
                    obj[key] = os.environ.get(env_var, value)
                else:
                    self._expand_env_vars(value)
        elif isinstance(obj, list):
            for item in obj:
                self._expand_env_vars(item)
    
    def generate_claude_desktop_config(self, master_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Claude Desktop configuration"""
        claude_config = {
            "mcpServers": {}
        }
        
        for server_name, server_config in master_config.get("mcp_servers", {}).items():
            claude_server = {
                "command": server_config["command"],
                "args": server_config["args"]
            }
            
            if "env" in server_config:
                claude_server["env"] = server_config["env"]
                
            if "cwd" in server_config:
                claude_server["cwd"] = server_config["cwd"]
                
            claude_config["mcpServers"][server_name] = claude_server
            
        return claude_config
    
    def generate_claude_code_commands(self, master_config: Dict[str, Any]) -> list:
        """Generate Claude Code mcp add commands"""
        commands = []
        
        for server_name, server_config in master_config.get("mcp_servers", {}).items():
            cmd_parts = ["claude", "mcp", "add", server_name, server_config["command"]]
            cmd_parts.extend(server_config["args"])
            
            # Note: Claude Code doesn't support env vars directly
            if "env" in server_config:
                commands.append(f"# WARNING: {server_name} requires environment variables:")
                for env_var, env_val in server_config["env"].items():
                    commands.append(f"# export {env_var}='{env_val}'")
                    
            commands.append(" ".join(f'"{part}"' if " " in part else part for part in cmd_parts))
            
        return commands
    
    def sync_all(self) -> None:
        """Sync all configurations"""
        print("🔄 Loading master configuration...")
        master_config = self.load_master_config()
        
        print("📝 Generating Claude Desktop config...")
        claude_desktop_config = self.generate_claude_desktop_config(master_config)
        claude_desktop_path = self.generated_dir / "claude_desktop_config.json"
        with open(claude_desktop_path, 'w') as f:
            json.dump(claude_desktop_config, f, indent=2)
        print(f"   → {claude_desktop_path}")
        
        print("📝 Generating Claude Code commands...")
        claude_code_commands = self.generate_claude_code_commands(master_config)
        claude_code_path = self.generated_dir / "claude_code_commands.sh"
        with open(claude_code_path, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write("# Generated Claude Code MCP commands\n\n")
            for cmd in claude_code_commands:
                f.write(f"{cmd}\n")
        os.chmod(claude_code_path, 0o755)
        print(f"   → {claude_code_path}")
        
        # Copy to actual locations if they exist
        self._deploy_configs(master_config)
        
        print("✅ Sync complete!")
    
    def _deploy_configs(self, master_config: Dict[str, Any]) -> None:
        """Deploy generated configs to their actual locations"""
        tools = master_config.get("tools", {})
        
        # Claude Desktop
        if "claude_desktop" in tools:
            config_path = Path(tools["claude_desktop"]["config_path"]).expanduser()
            source_path = self.generated_dir / "claude_desktop_config.json"
            
            if config_path.parent.exists():
                # Backup existing config
                if config_path.exists():
                    backup_path = self.project_root / "backups" / f"claude_desktop_config.json.bak"
                    self.project_root.joinpath("backups").mkdir(exist_ok=True)
                    shutil.copy2(config_path, backup_path)
                    
                # Deploy new config
                shutil.copy2(source_path, config_path)
                print(f"   ✅ Deployed to {config_path}")
            else:
                print(f"   ⚠️  Claude Desktop config directory doesn't exist: {config_path.parent}")

def main():
    parser = argparse.ArgumentParser(description="Truffaldino Configuration Sync Manager")
    parser.add_argument("--dry-run", action="store_true", help="Generate configs but don't deploy")
    args = parser.parse_args()
    
    # Find project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Load environment variables from .env if it exists
    env_file = project_root / "env" / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    
    sync_manager = SyncManager(project_root)
    sync_manager.sync_all()

if __name__ == "__main__":
    main()