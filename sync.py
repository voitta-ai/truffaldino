"""
Truffaldino Sync Module
Core synchronization logic for AI tool configurations
"""

import json
import os
import shutil
import subprocess
import tempfile
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import xml.etree.ElementTree as ET
from xml.dom import minidom

from config import (
    SUPPORTED_APPS, get_app_by_number, get_app_by_id,
    TRUFFALDINO_DIR, VERSIONS_DIR, CONFLICTS_LOG, 
    MAX_VERSIONS_PER_APP, TEMP_CONFLICT_FILE
)


class ConfigManager:
    """Manages loading and saving configurations for different AI tools"""
    
    def __init__(self):
        # Ensure Truffaldino directories exist
        TRUFFALDINO_DIR.mkdir(exist_ok=True)
        VERSIONS_DIR.mkdir(exist_ok=True)
    
    def detect_installed_apps(self) -> List[Tuple[int, str, bool]]:
        """Detect which AI applications are installed
        Returns: List of (number, app_name, is_installed)
        """
        results = []
        for i, app in enumerate(SUPPORTED_APPS):
            number = i + 1
            is_installed = False
            
            if app.id == "claude_code":
                # Special case: check if claude CLI is available
                is_installed = shutil.which("claude") is not None
            elif app.id == "cline":
                # Special case: check if Cline config file exists
                config_path = app.get_config_path()
                is_installed = config_path and config_path.exists()
            else:
                # Check if config path exists
                config_path = app.get_config_path()
                if config_path:
                    if app.id == "intellij":
                        # For IntelliJ, check if JetBrains directory exists
                        is_installed = config_path.exists()
                    else:
                        # For others, check if parent directory exists
                        is_installed = config_path.parent.exists()
            
            results.append((number, app.name, is_installed))
        
        return results
    
    def load_mcp_config(self, app_number: int) -> Optional[Dict[str, Any]]:
        """Load MCP configuration from an app"""
        app = get_app_by_number(app_number)
        if not app:
            return None
        
        if app.id == "claude_code":
            return self._load_claude_code_config()
        elif app.id == "intellij":
            return self._load_intellij_mcp_config()
        elif app.id == "cline":
            return self._load_cline_mcp_config()
        else:
            config_path = app.get_config_path()
            if config_path and config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                    return config.get("mcpServers", {})
                except Exception as e:
                    print(f"Error loading {app.name} config: {e}")
                    return None
        
        return None
    
    def save_mcp_config(self, app_number: int, mcp_servers: Dict[str, Any]) -> bool:
        """Save MCP configuration to an app"""
        app = get_app_by_number(app_number)
        if not app:
            return False
        
        # Create backup first
        self.create_backup(app_number)
        
        if app.id == "claude_code":
            return self._save_claude_code_config(mcp_servers)
        elif app.id == "intellij":
            return self._save_intellij_mcp_config(mcp_servers)
        elif app.id == "cline":
            return self._save_cline_mcp_config(mcp_servers)
        else:
            config_path = app.get_config_path()
            if not config_path:
                return False
            
            # Ensure directory exists
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Load existing config or create new
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                except:
                    config = {}
            else:
                config = {}
            
            # Update MCP servers
            config["mcpServers"] = mcp_servers
            
            # Save config
            try:
                with open(config_path, 'w') as f:
                    json.dump(config, f, indent=2, sort_keys=True)
                return True
            except Exception as e:
                print(f"Error saving {app.name} config: {e}")
                return False
    
    def load_prompt(self, app_number: int) -> Optional[Tuple[str, str]]:
        """Load prompt from an app. Returns (prompt_content, file_path)"""
        app = get_app_by_number(app_number)
        if not app or not app.has_prompt_support:
            return None
        
        if app.id == "intellij":
            return self._load_intellij_prompt()
        else:
            prompt_path = app.get_prompt_path()
            if prompt_path and prompt_path.exists():
                try:
                    with open(prompt_path, 'r') as f:
                        content = f.read()
                    return (content, str(prompt_path))
                except Exception as e:
                    print(f"Error loading {app.name} prompt: {e}")
                    return None
        
        return None
    
    def save_prompt(self, app_number: int, prompt_content: str) -> bool:
        """Save prompt to an app"""
        app = get_app_by_number(app_number)
        if not app or not app.has_prompt_support:
            return False
        
        if app.id == "intellij":
            return self._save_intellij_prompt(prompt_content)
        else:
            prompt_path = app.get_prompt_path()
            if not prompt_path:
                return False
            
            # Ensure directory exists
            prompt_path.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                with open(prompt_path, 'w') as f:
                    f.write(prompt_content)
                return True
            except Exception as e:
                print(f"Error saving {app.name} prompt: {e}")
                return False
    
    def create_backup(self, app_number: int) -> Optional[str]:
        """Create timestamped backup of app configuration"""
        app = get_app_by_number(app_number)
        if not app:
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if app.id == "claude_code":
            # For Claude Code, save current config list
            config = self._load_claude_code_config()
            if config:
                backup_name = f"claude_code_{timestamp}.json"
                backup_path = VERSIONS_DIR / backup_name
                with open(backup_path, 'w') as f:
                    json.dump(config, f, indent=2)
                self._cleanup_old_backups(app.id)
                return str(backup_path)
        else:
            config_path = app.get_config_path()
            if config_path and config_path.exists() and config_path.is_file():
                ext = config_path.suffix
                backup_name = f"{app.id}_{timestamp}{ext}"
                backup_path = VERSIONS_DIR / backup_name
                shutil.copy2(config_path, backup_path)
                self._cleanup_old_backups(app.id)
                return str(backup_path)
        
        return None
    
    def _load_cline_mcp_config(self) -> Optional[Dict[str, Any]]:
        """Load Cline MCP configuration from JSON file"""
        cline_app = get_app_by_id("cline")
        if not cline_app:
            return None
        
        config_path = cline_app.get_config_path()
        if not config_path or not config_path.exists():
            return None
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            return config.get("mcpServers", {})
        except Exception as e:
            print(f"Error loading Cline config: {e}")
            return None
    
    def _save_cline_mcp_config(self, mcp_servers: Dict[str, Any]) -> bool:
        """Save Cline MCP configuration to JSON file"""
        cline_app = get_app_by_id("cline")
        if not cline_app:
            return False
        
        config_path = cline_app.get_config_path()
        if not config_path:
            return False
        
        # Ensure directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing config or create new
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
            except:
                config = {}
        else:
            config = {}
        
        # Update MCP servers
        config["mcpServers"] = mcp_servers
        
        # Save config
        try:
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2, sort_keys=True)
            return True
        except Exception as e:
            print(f"Error saving Cline config: {e}")
            return False
    
    def _cleanup_old_backups(self, app_id: str):
        """Keep only the most recent MAX_VERSIONS_PER_APP backups"""
        pattern = f"{app_id}_*.json" if app_id == "claude_code" else f"{app_id}_*.*"
        backups = sorted(VERSIONS_DIR.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
        
        # Remove old backups
        for backup in backups[MAX_VERSIONS_PER_APP:]:
            backup.unlink()
    
    def _load_claude_code_config(self) -> Optional[Dict[str, Any]]:
        """Extract Claude Code configuration using CLI"""
        try:
            result = subprocess.run(
                ["claude", "mcp", "list", "--scope", "user"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return None
            
            # Parse the output to extract MCP servers
            # Format: "server_name: command arg1 arg2"
            servers = {}
            for line in result.stdout.strip().split('\n'):
                if ': ' in line and not line.startswith('No MCP servers'):
                    parts = line.split(': ', 1)
                    server_name = parts[0].strip()
                    command_parts = parts[1].strip().split()
                    
                    servers[server_name] = {
                        "command": command_parts[0],
                        "args": command_parts[1:] if len(command_parts) > 1 else []
                    }
            
            return servers
        except Exception:
            return None
    
    def _save_claude_code_config(self, mcp_servers: Dict[str, Any]) -> bool:
        """Save Claude Code configuration using CLI commands with superset sync logic"""
        try:
            # Load existing servers to implement superset sync
            existing_servers = self._load_claude_code_config() or {}
            
            # Create wrapper script directory
            wrapper_dir = Path.home() / ".claude-mcp-wrappers"
            wrapper_dir.mkdir(exist_ok=True)
            
            # Identify duplicates to remove (by name, then by command+args+env)
            duplicates_to_remove = self._find_duplicates(existing_servers, mcp_servers)
            
            # Remove only duplicate servers
            for server_name in duplicates_to_remove:
                print(f"Removing duplicate server: {server_name}")
                result = subprocess.run(
                    ["claude", "mcp", "remove", "--scope", "user", server_name],
                    capture_output=True,
                    timeout=5
                )
                if result.returncode != 0:
                    print(f"Warning: Failed to remove duplicate server {server_name}: {result.stderr.decode() if result.stderr else 'Unknown error'}")
            
            # Add new servers from source that don't exist in target
            for server_name, config in mcp_servers.items():
                # Skip if this server already exists (not a duplicate)
                if self._server_exists_in_target(server_name, config, existing_servers, duplicates_to_remove):
                    continue
                
                # Clean problematic args
                args = config.get("args", [])
                clean_args = self._clean_args(args)
                
                # Skip servers that use unsupported flags in Claude Code
                if args and any(arg in ["-m"] for arg in args):
                    print(f"Skipping {server_name} - contains unsupported flags for Claude Code")
                    continue
                
                command = config.get("command", "")
                env_vars = config.get("env", {})
                
                # Check if environment variables are needed
                if env_vars:
                    print(f"Creating wrapper script for {server_name} with environment variables")
                    
                    # Create wrapper script
                    wrapper_script = wrapper_dir / f"{server_name}.sh"
                    with open(wrapper_script, 'w') as f:
                        f.write("#!/bin/bash\n")
                        
                        # Add environment variable exports
                        for key, value in env_vars.items():
                            f.write(f'export {key}="{value}"\n')
                        
                        # Add the actual command
                        f.write(f"exec {command} {' '.join(clean_args)}\n")
                    
                    # Make wrapper script executable
                    wrapper_script.chmod(0o755)
                    
                    # Add to Claude Code using wrapper script with user scope
                    cmd = ["claude", "mcp", "add", "--scope", "user", server_name, str(wrapper_script)]
                else:
                    print(f"Adding server {server_name} directly (no env vars)")
                    cmd = ["claude", "mcp", "add", "--scope", "user", server_name, command] + clean_args
                
                result = subprocess.run(cmd, capture_output=True, timeout=5)
                if result.returncode != 0:
                    error_msg = result.stderr.decode() if result.stderr else 'Unknown error'
                    # Don't fail if server already exists - this is expected in some sync scenarios
                    if "already exists" in error_msg:
                        print(f"Warning: {server_name} already exists in Claude Code")
                    else:
                        print(f"Failed to add {server_name} (from {server_name}) to Claude Code: {error_msg}")
                        return False
            
            return True
        except Exception as e:
            print(f"Error updating Claude Code config: {e}")
            return False
    
    
    def _clean_args(self, args: List[str]) -> List[str]:
        """Clean problematic arguments like -y and --with fastmcp"""
        if not args:
            return []
        
        # Convert to string and clean
        args_str = " ".join(args)
        # Remove -y flag
        args_str = args_str.replace("-y", "")
        # Remove --with fastmcp
        args_str = args_str.replace("--with fastmcp", "")
        # Clean up multiple spaces
        args_str = " ".join(args_str.split())
        
        return args_str.split() if args_str.strip() else []
    
    def _find_duplicates(self, existing: Dict[str, Any], new_servers: Dict[str, Any]) -> List[str]:
        """Find duplicate servers to remove from existing servers"""
        duplicates = []
        
        for new_name, new_config in new_servers.items():
            # First check by name
            if new_name in existing:
                duplicates.append(new_name)
                continue
            
            # Then check by command, args, and env
            new_command = new_config.get("command", "")
            new_args = set(new_config.get("args", []))
            new_env = new_config.get("env", {})
            
            for existing_name, existing_config in existing.items():
                existing_command = existing_config.get("command", "")
                existing_args = set(existing_config.get("args", []))
                existing_env = existing_config.get("env", {})
                
                if (new_command == existing_command and 
                    new_args == existing_args and 
                    new_env == existing_env):
                    duplicates.append(existing_name)
                    break
        
        return duplicates
    
    def _server_exists_in_target(self, server_name: str, config: Dict[str, Any], 
                               existing: Dict[str, Any], duplicates: List[str]) -> bool:
        """Check if server already exists in target (excluding duplicates to be removed)"""
        # If it's in duplicates list, it will be removed, so we can add it
        if server_name in duplicates:
            return False
        
        # Check by name
        if server_name in existing:
            return True
        
        # Check by command, args, and env (excluding duplicates)
        command = config.get("command", "")
        args = set(config.get("args", []))
        env = config.get("env", {})
        
        for existing_name, existing_config in existing.items():
            if existing_name in duplicates:
                continue  # Skip duplicates that will be removed
            
            existing_command = existing_config.get("command", "")
            existing_args = set(existing_config.get("args", []))
            existing_env = existing_config.get("env", {})
            
            if (command == existing_command and 
                args == existing_args and 
                env == existing_env):
                return True
        
        return False
    
    def _find_intellij_config_dir(self) -> Optional[Path]:
        """Find the IntelliJ configuration directory"""
        base_path = Path.home()
        if os.name == 'posix':  # Unix-like (macOS, Linux)
            if Path("/System").exists():  # macOS
                base_path = base_path / "Library/Application Support/JetBrains"
            else:  # Linux
                base_path = base_path / ".config/JetBrains"
        else:  # Windows
            base_path = base_path / "AppData/Roaming/JetBrains"
        
        if not base_path.exists():
            return None
        
        # Find IntelliJ directories (e.g., IntelliJIdea2024.3)
        intellij_dirs = [d for d in base_path.iterdir() if d.is_dir() and d.name.startswith("IntelliJIdea")]
        if not intellij_dirs:
            return None
        
        # Use the most recent one
        return sorted(intellij_dirs)[-1] / "options"
    
    def _load_intellij_mcp_config(self) -> Optional[Dict[str, Any]]:
        """Load IntelliJ MCP configuration from XML"""
        options_dir = self._find_intellij_config_dir()
        if not options_dir:
            return None
        
        xml_path = options_dir / "llm.mcpServers.xml"
        if not xml_path.exists():
            return None
        
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            servers = {}
            # Parse XML structure - adjust based on actual IntelliJ format
            for server in root.findall(".//server"):
                name = server.get("name")
                if name:
                    servers[name] = {
                        "command": server.get("command", ""),
                        "args": server.get("args", "").split() if server.get("args") else [],
                        "env": {}
                    }
                    # Parse environment variables if present
                    for env in server.findall("env"):
                        key = env.get("key")
                        value = env.get("value")
                        if key:
                            servers[name]["env"][key] = value
            
            return servers
        except Exception as e:
            print(f"Error parsing IntelliJ XML: {e}")
            return None
    
    def _save_intellij_mcp_config(self, mcp_servers: Dict[str, Any]) -> bool:
        """Save IntelliJ MCP configuration to XML"""
        options_dir = self._find_intellij_config_dir()
        if not options_dir:
            return False
        
        options_dir.mkdir(parents=True, exist_ok=True)
        xml_path = options_dir / "llm.mcpServers.xml"
        
        try:
            # Create XML structure
            root = ET.Element("application")
            component = ET.SubElement(root, "component", name="LLMMcpServers")
            servers_elem = ET.SubElement(component, "servers")
            
            for server_name, config in mcp_servers.items():
                server_elem = ET.SubElement(servers_elem, "server",
                    name=server_name,
                    command=config.get("command", ""),
                    args=" ".join(config.get("args", []))
                )
                
                # Add environment variables if present
                if "env" in config and config["env"]:
                    for key, value in config["env"].items():
                        ET.SubElement(server_elem, "env", key=key, value=str(value))
            
            # Pretty print XML
            xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
            
            with open(xml_path, 'w') as f:
                f.write(xml_str)
            
            return True
        except Exception as e:
            print(f"Error saving IntelliJ XML: {e}")
            return False
    
    def _load_intellij_prompt(self) -> Optional[Tuple[str, str]]:
        """Load IntelliJ system prompt"""
        options_dir = self._find_intellij_config_dir()
        if not options_dir:
            return None
        
        prompt_path = options_dir / "ai_assistant_system_prompt.txt"
        if prompt_path.exists():
            try:
                with open(prompt_path, 'r') as f:
                    content = f.read()
                return (content, str(prompt_path))
            except Exception:
                return None
        
        return None
    
    def _save_intellij_prompt(self, prompt_content: str) -> bool:
        """Save IntelliJ system prompt"""
        options_dir = self._find_intellij_config_dir()
        if not options_dir:
            return False
        
        options_dir.mkdir(parents=True, exist_ok=True)
        prompt_path = options_dir / "ai_assistant_system_prompt.txt"
        
        try:
            with open(prompt_path, 'w') as f:
                f.write(prompt_content)
            return True
        except Exception:
            return False


class SyncEngine:
    """Core synchronization engine"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
    
    def sync_mcp_servers(self, from_app: int, to_app: int, mode: str = "smart") -> bool:
        """Sync MCP servers from one app to another
        
        Modes:
        - merge: Add missing servers only
        - replace: Replace all servers
        - smart: Interactive conflict resolution
        """
        # Load source configuration
        source_servers = self.config_manager.load_mcp_config(from_app)
        if source_servers is None:
            print(f"Failed to load configuration from app {from_app}")
            return False
        
        if not source_servers:
            print("No MCP servers found in source configuration")
            return False
        
        # Load target configuration
        target_servers = self.config_manager.load_mcp_config(to_app) or {}
        
        # Apply sync mode
        if mode == "replace":
            merged_servers = source_servers
        elif mode == "merge":
            merged_servers = {**target_servers, **source_servers}
        else:  # smart mode
            merged_servers = self._smart_merge(source_servers, target_servers)
        
        # Save to target
        success = self.config_manager.save_mcp_config(to_app, merged_servers)
        if success:
            print(f"Successfully synced {len(merged_servers)} MCP servers")
        
        return success
    
    def sync_prompts(self, from_app: int, to_app: int) -> bool:
        """Sync prompts from one app to another"""
        # Load source prompt
        source_prompt = self.config_manager.load_prompt(from_app)
        if not source_prompt:
            print(f"No prompt found in source app")
            return False
        
        prompt_content, source_path = source_prompt
        
        # Save to target
        success = self.config_manager.save_prompt(to_app, prompt_content)
        if success:
            print(f"Successfully synced prompt from {source_path}")
        
        return success
    
    def remove_all_mcp_servers(self, app_number: int) -> bool:
        """Remove all MCP servers from a specific app"""
        app = get_app_by_number(app_number)
        if not app:
            return False
        
        # Create backup first
        self.config_manager.create_backup(app_number)
        
        if app.id == "claude_code":
            return self._remove_all_claude_code_servers()
        else:
            # For other apps, save empty MCP servers configuration
            return self.config_manager.save_mcp_config(app_number, {})
    
    def _remove_all_claude_code_servers(self) -> bool:
        """Remove all MCP servers from Claude Code using CLI"""
        try:
            # Get list of current servers
            existing_servers = self.config_manager._load_claude_code_config() or {}
            
            if not existing_servers:
                print("No MCP servers found to remove from Claude Code")
                return True
            
            # Remove each server
            for server_name in existing_servers.keys():
                result = subprocess.run(
                    ["claude", "mcp", "remove", "--scope", "user", server_name],
                    capture_output=True,
                    timeout=5
                )
                if result.returncode != 0:
                    error_msg = result.stderr.decode() if result.stderr else 'Unknown error'
                    print(f"Warning: Failed to remove server {server_name}: {error_msg}")
                else:
                    print(f"Removed server: {server_name}")
            
            # Clean up wrapper scripts directory if it exists
            wrapper_dir = Path.home() / ".claude-mcp-wrappers"
            if wrapper_dir.exists():
                try:
                    shutil.rmtree(wrapper_dir)
                    print("Cleaned up wrapper scripts directory")
                except Exception as e:
                    print(f"Warning: Could not clean up wrapper scripts: {e}")
            
            return True
        except Exception as e:
            print(f"Error removing Claude Code servers: {e}")
            return False
    
    def _smart_merge(self, source: Dict[str, Any], target: Dict[str, Any]) -> Dict[str, Any]:
        """Smart merge with conflict detection"""
        conflicts = []
        merged = target.copy()
        
        # Detect conflicts
        for server_name, source_config in source.items():
            if server_name in target:
                if source_config != target[server_name]:
                    conflicts.append(server_name)
            else:
                merged[server_name] = source_config
        
        if conflicts:
            print(f"\nConflicts detected in: {', '.join(conflicts)}")
            print("Options:")
            print("1. Keep target (skip conflicts)")
            print("2. Use source (overwrite conflicts)")
            print("3. Review each conflict")
            
            choice = input("Choice (1-3): ").strip()
            
            if choice == "2":
                for server_name in conflicts:
                    merged[server_name] = source[server_name]
            elif choice == "3":
                for server_name in conflicts:
                    print(f"\nConflict in '{server_name}':")
                    print(f"Source: {json.dumps(source[server_name], indent=2)}")
                    print(f"Target: {json.dumps(target[server_name], indent=2)}")
                    use_source = input("Use source? (y/n): ").lower() == 'y'
                    if use_source:
                        merged[server_name] = source[server_name]
        
        return merged


class ConflictResolver:
    """Handles configuration conflicts via temp files"""
    
    @staticmethod
    def create_conflict_file(conflicts: List[Dict[str, Any]]) -> str:
        """Create a temporary conflict file for editing"""
        content = []
        content.append("# Truffaldino Configuration Conflicts")
        content.append("# Edit this file to resolve conflicts, then save and exit")
        content.append("# For each conflict, uncomment the configuration you want to keep")
        content.append("#" * 60)
        content.append("")
        
        for conflict in conflicts:
            server_name = conflict["server_name"]
            content.append(f"## Server: {server_name}")
            content.append("")
            
            content.append("### Option 1 (Source):")
            content.append(f"# {json.dumps(conflict['source'], indent=2)}")
            content.append("")
            
            content.append("### Option 2 (Target):")
            content.append(f"# {json.dumps(conflict['target'], indent=2)}")
            content.append("")
            
            content.append("### Your choice (uncomment one):")
            content.append(f"# KEEP: source")
            content.append(f"# KEEP: target")
            content.append("")
            content.append("-" * 60)
            content.append("")
        
        # Write to temp file
        with open(TEMP_CONFLICT_FILE, 'w') as f:
            f.write('\n'.join(content))
        
        return TEMP_CONFLICT_FILE
    
    @staticmethod
    def parse_conflict_file(filepath: str) -> Dict[str, str]:
        """Parse the edited conflict file to get resolutions"""
        resolutions = {}
        current_server = None
        
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith("## Server:"):
                    current_server = line.split("## Server:")[1].strip()
                elif line.startswith("KEEP:") and current_server:
                    choice = line.split("KEEP:")[1].strip()
                    resolutions[current_server] = choice
        
        return resolutions
