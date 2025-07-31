#!/usr/bin/env python3
"""
Smart Import - Sophisticated config detection and merging
Detects all available AI tool configs and creates an intelligent superset
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
import tempfile
import shutil
from collections import OrderedDict

class ConfigDetector:
    """Detect and analyze AI tool configurations"""
    
    # Known config locations for various tools
    CONFIG_LOCATIONS = {
        "claude_desktop": [
            Path.home() / "Library/Application Support/Claude/claude_desktop_config.json",  # macOS
            Path.home() / ".config/claude/config.json",  # Linux
            Path.home() / "AppData/Roaming/Claude/config.json",  # Windows
        ],
        "claude_code": [
            # Claude Code uses commands rather than a config file
            # We'll check if claude CLI exists and extract config
        ],
        "cline": [
            Path.home() / ".cline/mcp_settings.json",
        ],
        "jetbrains": [
            Path.home() / "Library/Application Support/JetBrains/IntelliJIdea2024.3/options/llm.mcpServers.xml",
            Path.home() / ".config/JetBrains/IntelliJIdea2024.3/options/llm.mcpServers.xml",
        ],
        "windsurf": [
            Path.home() / ".windsurf/mcp.json",
        ],
        "cursor": [
            Path.home() / ".cursor/mcp_config.json",
        ],
    }
    
    def __init__(self):
        self.found_configs = {}
        self.version_dir = Path.home() / ".truffaldino" / "versions"
        self.version_dir.mkdir(parents=True, exist_ok=True)
        
    def detect_configs(self) -> Dict[str, Tuple[Path, datetime]]:
        """Detect all available config files with their modification times"""
        configs = {}
        
        for tool_name, paths in self.CONFIG_LOCATIONS.items():
            for path in paths:
                if path.exists():
                    mod_time = datetime.fromtimestamp(path.stat().st_mtime)
                    configs[tool_name] = (path, mod_time)
                    break
        
        # Special case: Claude Code
        if shutil.which("claude"):
            try:
                # Try to get Claude Code MCP list
                result = subprocess.run(
                    ["claude", "mcp", "list"], 
                    capture_output=True, 
                    text=True,
                    timeout=5
                )
                if result.returncode == 0 and "No MCP servers configured" not in result.stdout:
                    # Claude Code has some configs
                    configs["claude_code"] = (None, datetime.now())
            except:
                pass
                
        return configs
    
    def load_config(self, tool_name: str, path: Optional[Path]) -> Dict[str, Any]:
        """Load configuration from a specific tool"""
        if tool_name == "claude_code" and path is None:
            return self._extract_claude_code_config()
        
        if not path or not path.exists():
            return {}
            
        if path.suffix == ".json":
            with open(path, 'r') as f:
                return json.load(f)
        elif path.suffix == ".xml":
            # TODO: Parse XML configs (JetBrains)
            return {}
        
        return {}
    
    def _extract_claude_code_config(self) -> Dict[str, Any]:
        """Extract Claude Code configuration using CLI"""
        config = {"mcpServers": {}}
        
        try:
            result = subprocess.run(
                ["claude", "mcp", "list"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Parse the output to reconstruct config
                # This is a simplified version - would need more robust parsing
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if ':' in line and not line.startswith("Checking"):
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            server_name = parts[0].strip()
                            command_args = parts[1].strip()
                            # Basic parsing - would need enhancement
                            config["mcpServers"][server_name] = {
                                "command": command_args.split()[0] if command_args else "",
                                "args": command_args.split()[1:] if len(command_args.split()) > 1 else []
                            }
        except:
            pass
            
        return config
    
    def create_superset(self, configs: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Create a superset of all configurations with conflict detection"""
        superset = {"mcpServers": OrderedDict()}
        conflicts = []
        
        # Track which tools provide which servers
        server_sources = {}
        
        for tool_name, config in configs.items():
            mcp_servers = config.get("mcpServers", {})
            
            for server_name, server_config in mcp_servers.items():
                if server_name not in superset["mcpServers"]:
                    # New server, add it
                    superset["mcpServers"][server_name] = server_config
                    server_sources[server_name] = [tool_name]
                else:
                    # Server exists, check for conflicts
                    server_sources[server_name].append(tool_name)
                    existing = superset["mcpServers"][server_name]
                    
                    # Check for differences
                    if self._configs_differ(existing, server_config):
                        conflicts.append({
                            "server": server_name,
                            "tools": server_sources[server_name],
                            "configs": {
                                server_sources[server_name][0]: existing,
                                tool_name: server_config
                            }
                        })
        
        # Sort the servers alphabetically
        superset["mcpServers"] = OrderedDict(
            sorted(superset["mcpServers"].items())
        )
        
        return superset, conflicts, server_sources
    
    def _configs_differ(self, config1: Dict, config2: Dict) -> bool:
        """Check if two server configs differ significantly"""
        # Compare command
        if config1.get("command") != config2.get("command"):
            return True
            
        # Compare args (order matters)
        args1 = config1.get("args", [])
        args2 = config2.get("args", [])
        if args1 != args2:
            return True
            
        # Compare env vars
        env1 = config1.get("env", {})
        env2 = config2.get("env", {})
        if env1 != env2:
            return True
            
        # Compare cwd
        if config1.get("cwd") != config2.get("cwd"):
            return True
            
        return False
    
    def version_file(self, file_path: Path) -> str:
        """Create a versioned backup of a file using RCS-style naming"""
        if not file_path.exists():
            return ""
            
        # Create version filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        version_name = f"{file_path.name}.{timestamp}"
        version_path = self.version_dir / version_name
        
        # Copy file to version directory
        shutil.copy2(file_path, version_path)
        
        # Keep last 10 versions
        versions = sorted(self.version_dir.glob(f"{file_path.name}.*"))
        if len(versions) > 10:
            for old_version in versions[:-10]:
                old_version.unlink()
                
        return str(version_path)
    
    def create_annotated_json(self, superset: Dict, conflicts: List, 
                            server_sources: Dict[str, List[str]]) -> str:
        """Create JSON with comments about conflicts and sources"""
        lines = []
        lines.append("{")
        lines.append('  "mcpServers": {')
        
        servers = list(superset["mcpServers"].items())
        for i, (server_name, server_config) in enumerate(servers):
            # Add comment about sources
            sources = server_sources.get(server_name, [])
            if len(sources) > 1:
                lines.append(f'    // {server_name}: Found in {", ".join(sources)}')
            else:
                lines.append(f'    // {server_name}: From {sources[0] if sources else "unknown"}')
            
            # Check if this server has conflicts
            conflict_info = next((c for c in conflicts if c["server"] == server_name), None)
            if conflict_info:
                lines.append(f'    // ⚠️  CONFLICT: Different configs in {", ".join(conflict_info["tools"])}')
                for tool, config in conflict_info["configs"].items():
                    if config.get("env"):
                        env_vars = ", ".join(config["env"].keys())
                        lines.append(f'    //   {tool} env: {env_vars}')
            
            # Output the server config
            lines.append(f'    "{server_name}": {json.dumps(server_config, indent=6)}'.rstrip())
            
            if i < len(servers) - 1:
                lines[-1] += ","
                
        lines.append("  }")
        lines.append("}")
        
        return "\n".join(lines)
    
    def convert_claude_config_to_master(self, claude_config: Dict[str, Any]) -> Dict[str, Any]:
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
    print("🔍 Truffaldino Smart Import")
    print("=" * 50)
    
    detector = ConfigDetector()
    
    # Detect all configs
    print("\n📂 Detecting configuration files...")
    found_configs = detector.detect_configs()
    
    if not found_configs:
        print("❌ No configuration files found!")
        return 1
    
    # Display found configs
    print("\n✅ Found configurations:")
    for tool_name, (path, mod_time) in found_configs.items():
        path_str = str(path) if path else "CLI-based config"
        print(f"  • {tool_name:15} {path_str}")
        print(f"    Last modified: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load all configs
    print("\n📖 Loading configurations...")
    loaded_configs = {}
    for tool_name, (path, _) in found_configs.items():
        config = detector.load_config(tool_name, path)
        if config:
            loaded_configs[tool_name] = config
            server_count = len(config.get("mcpServers", {}))
            print(f"  • {tool_name}: {server_count} MCP servers")
    
    # Create superset
    print("\n🔄 Creating superset configuration...")
    superset, conflicts, server_sources = detector.create_superset(loaded_configs)
    
    # Report findings
    total_servers = len(superset["mcpServers"])
    print(f"\n📊 Analysis complete:")
    print(f"  • Total unique MCP servers: {total_servers}")
    print(f"  • Conflicts detected: {len(conflicts)}")
    
    if conflicts:
        print("\n⚠️  Conflicts found:")
        for conflict in conflicts:
            print(f"  • {conflict['server']}: Different configs in {', '.join(conflict['tools'])}")
    
    # Create annotated JSON
    annotated_json = detector.create_annotated_json(superset, conflicts, server_sources)
    
    # Write to temporary file for editing
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        tmp.write(annotated_json)
        tmp_path = Path(tmp.name)
    
    # Open in editor
    editor = os.environ.get('EDITOR', 'vim')
    print(f"\n📝 Opening configuration in {editor}...")
    print("   Review and edit the superset configuration.")
    print("   Comments show sources and conflicts.")
    print("   Save and exit when done.")
    
    subprocess.run([editor, str(tmp_path)])
    
    # Read back the edited content
    with open(tmp_path, 'r') as f:
        edited_content = f.read()
    
    # Remove comments for final JSON
    import re
    clean_json = re.sub(r'^\s*//.*$', '', edited_content, flags=re.MULTILINE)
    clean_json = '\n'.join(line for line in clean_json.split('\n') if line.strip())
    
    # Validate JSON
    try:
        final_config = json.loads(clean_json)
    except json.JSONDecodeError as e:
        print(f"\n❌ Invalid JSON after editing: {e}")
        print("   The edited file is saved at:", tmp_path)
        return 1
    
    # Version existing configs
    print("\n💾 Creating backups...")
    project_root = Path(__file__).parent.parent
    target_file = project_root / "configs" / "generated" / "claude_desktop_config.json"
    
    if target_file.exists():
        backup_path = detector.version_file(target_file)
        print(f"  • Backed up to: {backup_path}")
    
    # Save the final config
    target_file.parent.mkdir(parents=True, exist_ok=True)
    with open(target_file, 'w') as f:
        json.dump(final_config, f, indent=2, sort_keys=True)
    
    print(f"\n✅ Superset configuration saved to: {target_file}")
    
    # Save primary config location
    primary_config = project_root / "configs" / "truffaldino.json"
    primary_config.parent.mkdir(parents=True, exist_ok=True)
    
    if primary_config.exists():
        backup_path = detector.version_file(primary_config)
        print(f"  • Backed up to: {backup_path}")
    
    with open(primary_config, 'w') as f:
        json.dump(final_config, f, indent=2, sort_keys=True)
    
    print(f"✅ Primary config saved: {primary_config}")
    
    # Cleanup
    tmp_path.unlink()
    
    print("\n🎉 Import complete!")
    print("\nNext steps:")
    print("1. Review configs/truffaldino.json")
    print("2. Update env/.env with any new API keys")
    print("3. Run ./scripts/sync.sh to sync to other tools")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())