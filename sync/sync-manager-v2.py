#!/usr/bin/env python3
"""
Truffaldino Sync Manager V2
Direct JSON-based synchronization between AI tools
"""

import os
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import argparse
from dotenv import load_dotenv
from datetime import datetime

class ConfigDetector:
    """Detect AI tool configurations"""
    
    CONFIG_LOCATIONS = {
        "claude_desktop": {
            "paths": [
                Path.home() / "Library/Application Support/Claude/claude_desktop_config.json",  # macOS
                Path.home() / ".config/claude/config.json",  # Linux
                Path.home() / "AppData/Roaming/Claude/config.json",  # Windows
            ],
            "format": "json",
            "description": "Claude Desktop"
        },
        "cline": {
            "paths": [
                Path.home() / ".cline/mcp_settings.json",
            ],
            "format": "json", 
            "description": "Cline"
        },
        "windsurf": {
            "paths": [
                Path.home() / ".windsurf/mcp.json",
            ],
            "format": "json",
            "description": "Windsurf"
        },
        "cursor": {
            "paths": [
                Path.home() / ".cursor/mcp_config.json",
            ],
            "format": "json",
            "description": "Cursor"
        }
    }
    
    def detect_configs(self) -> Dict[str, Tuple[Path, str, bool]]:
        """Detect all available config files
        Returns: {tool_name: (path, description, exists)}
        """
        configs = {}
        
        for tool_name, info in self.CONFIG_LOCATIONS.items():
            for path in info["paths"]:
                if path.parent.exists():  # Directory exists
                    configs[tool_name] = (
                        path,
                        info["description"],
                        path.exists()
                    )
                    break
                    
        return configs

class SyncManagerV2:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.version_dir = Path.home() / ".truffaldino" / "versions"
        self.version_dir.mkdir(parents=True, exist_ok=True)
        
        # Load environment
        env_file = project_root / "env" / ".env"
        if env_file.exists():
            load_dotenv(env_file)
            
        self.detector = ConfigDetector()
        
    def backup_config(self, path: Path, tool_name: str) -> str:
        """Create timestamped backup of config file"""
        if not path.exists():
            return ""
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{tool_name}_config_{timestamp}.json"
        backup_path = self.version_dir / backup_name
        
        shutil.copy2(path, backup_path)
        return str(backup_path)
    
    def load_json_config(self, path: Path) -> Optional[Dict[str, Any]]:
        """Load JSON config file"""
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except:
            return None
    
    def save_json_config(self, path: Path, config: Dict[str, Any]) -> bool:
        """Save JSON config file"""
        try:
            # Ensure directory exists
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w') as f:
                json.dump(config, f, indent=2, sort_keys=True)
            return True
        except Exception as e:
            print(f"❌ Error saving {path}: {e}")
            return False
    
    def sync_mcp_servers(self, source_config: Dict[str, Any], 
                        target_config: Dict[str, Any],
                        mode: str = "merge") -> Dict[str, Any]:
        """Sync MCP servers between configs
        
        Modes:
        - merge: Add missing servers from source to target
        - replace: Replace target servers with source servers
        - smart: Merge with conflict resolution
        """
        source_servers = source_config.get("mcpServers", {})
        target_servers = target_config.get("mcpServers", {})
        
        if mode == "replace":
            target_config["mcpServers"] = source_servers
        elif mode == "merge":
            # Add servers that don't exist in target
            for server_name, server_config in source_servers.items():
                if server_name not in target_servers:
                    target_servers[server_name] = server_config
            target_config["mcpServers"] = target_servers
        elif mode == "smart":
            # Show conflicts and let user decide
            conflicts = []
            for server_name in source_servers:
                if server_name in target_servers:
                    if source_servers[server_name] != target_servers[server_name]:
                        conflicts.append(server_name)
            
            if conflicts:
                print(f"\n⚠️  Conflicts found in: {', '.join(conflicts)}")
                print("How to handle conflicts?")
                print("1. Keep target (skip conflicts)")
                print("2. Use source (overwrite conflicts)")
                print("3. Review each conflict")
                
                choice = input("Choice (1-3): ").strip()
                
                if choice == "2":
                    for server_name in conflicts:
                        target_servers[server_name] = source_servers[server_name]
                elif choice == "3":
                    for server_name in conflicts:
                        print(f"\n🔄 Conflict in '{server_name}':")
                        print("Source:", json.dumps(source_servers[server_name], indent=2))
                        print("Target:", json.dumps(target_servers[server_name], indent=2))
                        use_source = input("Use source? (y/n): ").lower() == 'y'
                        if use_source:
                            target_servers[server_name] = source_servers[server_name]
            
            # Add non-conflicting servers
            for server_name, server_config in source_servers.items():
                if server_name not in target_servers:
                    target_servers[server_name] = server_config
                    
            target_config["mcpServers"] = target_servers
            
        return target_config
    
    def interactive_sync(self):
        """Interactive sync workflow"""
        print("🎪 Truffaldino Interactive Sync")
        print("=" * 50)
        
        # Detect available configs
        configs = self.detector.detect_configs()
        
        if not configs:
            print("❌ No AI tool configurations found!")
            return
        
        # Show detected configs
        print("\n📂 Detected configurations:")
        available_tools = []
        for i, (tool_name, (path, desc, exists)) in enumerate(configs.items()):
            status = "✅" if exists else "➕"
            print(f"{i+1}. {status} {desc:15} {path}")
            if exists:
                available_tools.append((tool_name, path, desc))
        
        if not available_tools:
            print("\n❌ No existing configurations found to sync from!")
            return
        
        # Choose source
        print("\n📤 Select source configuration:")
        for i, (tool_name, path, desc) in enumerate(available_tools):
            print(f"{i+1}. {desc}")
            
        source_idx = int(input("Source (number): ")) - 1
        source_tool, source_path, source_desc = available_tools[source_idx]
        
        # Load source config
        source_config = self.load_json_config(source_path)
        if not source_config:
            print(f"❌ Failed to load {source_desc} config")
            return
            
        server_count = len(source_config.get("mcpServers", {}))
        print(f"\n✅ Loaded {server_count} MCP servers from {source_desc}")
        
        # Choose targets
        print("\n📥 Select target configurations (comma-separated numbers, or 'all'):")
        all_tools = list(configs.items())
        for i, (tool_name, (path, desc, exists)) in enumerate(all_tools):
            if tool_name != source_tool:
                status = "exists" if exists else "will create"
                print(f"{i+1}. {desc:15} ({status})")
        
        target_input = input("Targets: ").strip()
        
        if target_input.lower() == 'all':
            target_indices = [i for i, (t, _) in enumerate(all_tools) if t != source_tool]
        else:
            target_indices = [int(x.strip())-1 for x in target_input.split(',')]
        
        # Choose sync mode
        print("\n🔄 Select sync mode:")
        print("1. Merge - Add missing servers only")
        print("2. Replace - Replace all servers") 
        print("3. Smart - Merge with conflict resolution")
        
        mode_choice = input("Mode (1-3): ").strip()
        mode_map = {"1": "merge", "2": "replace", "3": "smart"}
        sync_mode = mode_map.get(mode_choice, "merge")
        
        # Perform sync
        print(f"\n🚀 Syncing with mode: {sync_mode}")
        
        success_count = 0
        for idx in target_indices:
            tool_name, (path, desc, exists) = all_tools[idx]
            print(f"\n📝 Syncing to {desc}...")
            
            # Backup if exists
            if exists:
                backup_path = self.backup_config(path, tool_name)
                if backup_path:
                    print(f"  💾 Backed up to {Path(backup_path).name}")
            
            # Load or create target config
            if exists:
                target_config = self.load_json_config(path) or {"mcpServers": {}}
            else:
                target_config = {"mcpServers": {}}
            
            # Sync configs
            updated_config = self.sync_mcp_servers(source_config, target_config, sync_mode)
            
            # Save
            if self.save_json_config(path, updated_config):
                print(f"  ✅ Saved to {path}")
                success_count += 1
            else:
                print(f"  ❌ Failed to save")
        
        # Handle Claude Code special case
        if any(all_tools[idx][0] == "claude_code" for idx in target_indices):
            print("\n📝 Generating Claude Code commands...")
            self.generate_claude_code_commands(source_config)
        
        print(f"\n🎉 Sync complete! Updated {success_count} configurations")
        print("\n💡 Remember to restart AI tools to load new MCP servers")
    
    def generate_claude_code_commands(self, config: Dict[str, Any]):
        """Generate Claude Code CLI commands"""
        commands_file = self.project_root / "configs" / "generated" / "claude_code_commands.sh"
        commands_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(commands_file, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write("# Claude Code MCP server setup commands\n\n")
            
            f.write("# First, remove all existing servers\n")
            f.write("claude mcp list | grep -v 'No MCP servers' | cut -d':' -f1 | xargs -I {} claude mcp remove {}\n\n")
            
            f.write("# Add servers\n")
            for server_name, server_config in config.get("mcpServers", {}).items():
                cmd = server_config.get("command", "")
                args = server_config.get("args", [])
                
                # Note about env vars if present
                if "env" in server_config:
                    f.write(f"# {server_name} requires environment variables:\n")
                    for env_var in server_config["env"]:
                        f.write(f"# export {env_var}=...\n")
                
                # Build command
                cmd_line = f'claude mcp add "{server_name}" "{cmd}"'
                for arg in args:
                    cmd_line += f' "{arg}"'
                f.write(f"{cmd_line}\n\n")
        
        os.chmod(commands_file, 0o755)
        print(f"  📄 Claude Code commands saved to: {commands_file}")
        print(f"     Run with: {commands_file}")

def main():
    parser = argparse.ArgumentParser(description="Truffaldino Sync Manager V2")
    parser.add_argument("--source", help="Source tool name")
    parser.add_argument("--target", help="Target tool name(s), comma-separated")
    parser.add_argument("--mode", choices=["merge", "replace", "smart"], default="merge",
                       help="Sync mode")
    parser.add_argument("--list", action="store_true", help="List detected configs and exit")
    
    args = parser.parse_args()
    
    # Find project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    sync_manager = SyncManagerV2(project_root)
    
    if args.list:
        configs = sync_manager.detector.detect_configs()
        print("🔍 Detected configurations:")
        for tool_name, (path, desc, exists) in configs.items():
            status = "exists" if exists else "not found"
            print(f"  • {tool_name:15} {status:10} {path}")
        return
    
    # Interactive mode is default
    sync_manager.interactive_sync()

if __name__ == "__main__":
    main()