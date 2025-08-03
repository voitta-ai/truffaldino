#!/usr/bin/env python3
"""
Truffaldino MCP Server
Provides access to Truffaldino functionality via Model Context Protocol
"""

import sys
import json
import os
import subprocess
import tempfile
from typing import Any, Dict, List, Optional

# Try to import MCP dependencies
try:
    from mcp.server import Server, NotificationOptions
    from mcp.server.models import InitializationOptions
    import mcp.server.stdio
    import mcp.types as types
except ImportError:
    print("Error: MCP dependencies not found. Install with: pip install mcp", file=sys.stderr)
    sys.exit(1)

from config import SUPPORTED_APPS, get_app_by_number, TEMP_CONFLICT_FILE
from sync import ConfigManager, SyncEngine, ConflictResolver, ConflictDetectedException


class TruffaldinoMCPServer:
    """Truffaldino MCP Server implementation"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.sync_engine = SyncEngine()
        
        self.server = Server("truffaldino")
        self.setup_handlers()
    
    def setup_handlers(self):
        """Set up MCP request handlers"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[types.Tool]:
            """List available Truffaldino tools"""
            return [
                types.Tool(
                    name="truffaldino_list_apps",
                    description="List all supported AI applications and their installation status",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                types.Tool(
                    name="truffaldino_show_mcps",
                    description="Show MCP servers configured for a specific AI application",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "app_number": {
                                "type": "integer",
                                "description": "Application number (1-5)",
                                "minimum": 1,
                                "maximum": 5
                            }
                        },
                        "required": ["app_number"]
                    }
                ),
                types.Tool(
                    name="truffaldino_sync_mcps",
                    description="Sync MCP servers from one AI application to another",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "from_app": {
                                "type": "integer",
                                "description": "Source application number (1-5)",
                                "minimum": 1,
                                "maximum": 5
                            },
                            "to_app": {
                                "type": "integer",
                                "description": "Target application number (1-5)",
                                "minimum": 1,
                                "maximum": 5
                            },
                            "mode": {
                                "type": "string",
                                "description": "Sync mode: merge, replace, or smart",
                                "enum": ["merge", "replace", "smart"],
                                "default": "smart"
                            }
                        },
                        "required": ["from_app", "to_app"]
                    }
                ),
                types.Tool(
                    name="truffaldino_show_prompts",
                    description="Show system prompt for a specific AI application",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "app_number": {
                                "type": "integer",
                                "description": "Application number (1-5)",
                                "minimum": 1,
                                "maximum": 5
                            }
                        },
                        "required": ["app_number"]
                    }
                ),
                types.Tool(
                    name="truffaldino_sync_prompts",
                    description="Sync system prompts from one AI application to another",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "from_app": {
                                "type": "integer",
                                "description": "Source application number (1-5)",
                                "minimum": 1,
                                "maximum": 5
                            },
                            "to_app": {
                                "type": "integer",
                                "description": "Target application number (1-5)",
                                "minimum": 1,
                                "maximum": 5
                            }
                        },
                        "required": ["from_app", "to_app"]
                    }
                ),
                types.Tool(
                    name="truffaldino_status",
                    description="Show Truffaldino system status and configuration health",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                types.Tool(
                    name="truffaldino_resolve_conflicts",
                    description="Handle configuration conflicts via temporary file editing",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "conflicts": {
                                "type": "array",
                                "description": "List of conflicts to resolve",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "server_name": {"type": "string"},
                                        "source": {"type": "object"},
                                        "target": {"type": "object"}
                                    },
                                    "required": ["server_name", "source", "target"]
                                }
                            }
                        },
                        "required": ["conflicts"]
                    }
                ),
                types.Tool(
                    name="truffaldino_remove_all_mcps",
                    description="Remove all MCP servers from a specific AI application",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "app_number": {
                                "type": "integer",
                                "description": "Application number (1-5)",
                                "minimum": 1,
                                "maximum": 5
                            }
                        },
                        "required": ["app_number"]
                    }
                ),
                types.Tool(
                    name="truffaldino_resolve_conflict_keep_target",
                    description="Resolve all conflicts by keeping target configurations",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "from_app": {
                                "type": "integer",
                                "description": "Source application number (1-5)",
                                "minimum": 1,
                                "maximum": 5
                            },
                            "to_app": {
                                "type": "integer",
                                "description": "Target application number (1-5)",
                                "minimum": 1,
                                "maximum": 5
                            }
                        },
                        "required": ["from_app", "to_app"]
                    }
                ),
                types.Tool(
                    name="truffaldino_resolve_conflict_use_source",
                    description="Resolve all conflicts by using source configurations",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "from_app": {
                                "type": "integer",
                                "description": "Source application number (1-5)",
                                "minimum": 1,
                                "maximum": 5
                            },
                            "to_app": {
                                "type": "integer",
                                "description": "Target application number (1-5)",
                                "minimum": 1,
                                "maximum": 5
                            }
                        },
                        "required": ["from_app", "to_app"]
                    }
                ),
                types.Tool(
                    name="truffaldino_resolve_conflict_individual",
                    description="Resolve conflicts individually by specifying choices for each server",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "from_app": {
                                "type": "integer",
                                "description": "Source application number (1-5)",
                                "minimum": 1,
                                "maximum": 5
                            },
                            "to_app": {
                                "type": "integer",
                                "description": "Target application number (1-5)",
                                "minimum": 1,
                                "maximum": 5
                            },
                            "resolutions": {
                                "type": "object",
                                "description": "Map of server names to resolution choices ('source' or 'target')",
                                "additionalProperties": {
                                    "type": "string",
                                    "enum": ["source", "target"]
                                }
                            }
                        },
                        "required": ["from_app", "to_app", "resolutions"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
            """Handle tool calls"""
            
            if name == "truffaldino_list_apps":
                return await self.handle_list_apps()
            
            elif name == "truffaldino_show_mcps":
                app_number = arguments.get("app_number")
                return await self.handle_show_mcps(app_number)
            
            elif name == "truffaldino_sync_mcps":
                from_app = arguments.get("from_app")
                to_app = arguments.get("to_app")
                mode = arguments.get("mode", "smart")
                return await self.handle_sync_mcps(from_app, to_app, mode)
            
            elif name == "truffaldino_show_prompts":
                app_number = arguments.get("app_number")
                return await self.handle_show_prompts(app_number)
            
            elif name == "truffaldino_sync_prompts":
                from_app = arguments.get("from_app")
                to_app = arguments.get("to_app")
                return await self.handle_sync_prompts(from_app, to_app)
            
            elif name == "truffaldino_status":
                return await self.handle_status()
            
            elif name == "truffaldino_resolve_conflicts":
                conflicts = arguments.get("conflicts", [])
                return await self.handle_resolve_conflicts(conflicts)
            
            elif name == "truffaldino_remove_all_mcps":
                app_number = arguments.get("app_number")
                return await self.handle_remove_all_mcps(app_number)
            
            elif name == "truffaldino_resolve_conflict_keep_target":
                from_app = arguments.get("from_app")
                to_app = arguments.get("to_app")
                return await self.handle_resolve_conflict_keep_target(from_app, to_app)
            
            elif name == "truffaldino_resolve_conflict_use_source":
                from_app = arguments.get("from_app")
                to_app = arguments.get("to_app")
                return await self.handle_resolve_conflict_use_source(from_app, to_app)
            
            elif name == "truffaldino_resolve_conflict_individual":
                from_app = arguments.get("from_app")
                to_app = arguments.get("to_app")
                resolutions = arguments.get("resolutions", {})
                return await self.handle_resolve_conflict_individual(from_app, to_app, resolutions)
            
            else:
                return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
    
    async def handle_list_apps(self) -> List[types.TextContent]:
        """Handle list_apps tool call"""
        try:
            result = []
            result.append("Truffaldino - Supported AI Applications\n")
            
            detected_apps = self.config_manager.detect_installed_apps()
            
            for number, app_name, is_installed in detected_apps:
                status = "[INSTALLED]" if is_installed else "[NOT FOUND]"
                result.append(f"{number}. {app_name:15} {status}")
            
            return [types.TextContent(type="text", text="\n".join(result))]
        
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error listing apps: {str(e)}")]
    
    async def handle_show_mcps(self, app_number: int) -> List[types.TextContent]:
        """Handle show_mcps tool call"""
        try:
            app = get_app_by_number(app_number)
            if not app:
                return [types.TextContent(type="text", text=f"Invalid app number: {app_number}")]
            
            result = []
            result.append(f"MCP Servers for {app.name}\n")
            
            if not app.has_mcp_support:
                result.append(f"{app.name} does not support MCP servers")
                return [types.TextContent(type="text", text="\n".join(result))]
            
            servers = self.config_manager.load_mcp_config(app_number)
            if servers is None:
                result.append(f"Failed to load configuration from {app.name}")
                return [types.TextContent(type="text", text="\n".join(result))]
            
            if not servers:
                result.append("No MCP servers configured")
                return [types.TextContent(type="text", text="\n".join(result))]
            
            for server_name, config in servers.items():
                result.append(f"* {server_name}")
                result.append(f"   Command: {config.get('command', 'N/A')}")
                if config.get('args'):
                    result.append(f"   Args: {' '.join(config['args'])}")
                if config.get('env'):
                    result.append(f"   Environment: {list(config['env'].keys())}")
                result.append("")
            
            result.append(f"Total: {len(servers)} MCP servers")
            
            return [types.TextContent(type="text", text="\n".join(result))]
        
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error showing MCP servers: {str(e)}")]
    
    async def handle_sync_mcps(self, from_app: int, to_app: int, mode: str) -> List[types.TextContent]:
        """Handle sync_mcps tool call"""
        try:
            from_app_obj = get_app_by_number(from_app)
            to_app_obj = get_app_by_number(to_app)
            
            if not from_app_obj or not to_app_obj:
                return [types.TextContent(type="text", text="Invalid app numbers")]
            
            if not from_app_obj.has_mcp_support or not to_app_obj.has_mcp_support:
                return [types.TextContent(type="text", text="One or both apps don't support MCP servers")]
            
            # Use MCP mode for conflict resolution
            success = self.sync_engine.sync_mcp_servers(from_app, to_app, use_mcp_mode=True)
            
            if success:
                result = f"[SUCCESS] Synced MCP servers from {from_app_obj.name} to {to_app_obj.name}"
            else:
                result = f"[FAILED] Could not sync MCP servers from {from_app_obj.name} to {to_app_obj.name}"
            
            return [types.TextContent(type="text", text=result)]
        
        except ConflictDetectedException as e:
            # Handle conflicts detected in MCP mode
            result = []
            result.append(f"[CONFLICTS DETECTED] Found {len(e.conflict_names)} conflicts during sync:")
            result.append("")
            
            for conflict in e.conflict_data:
                server_name = conflict["server_name"]
                result.append(f"• Server: {server_name}")
                result.append(f"  Source config: {json.dumps(conflict['source'], indent=2)}")
                result.append(f"  Target config: {json.dumps(conflict['target'], indent=2)}")
                result.append("")
            
            result.append("To resolve conflicts, use one of these MCP tools:")
            result.append("1. truffaldino_resolve_conflict_keep_target - Keep all target configurations")
            result.append("2. truffaldino_resolve_conflict_use_source - Use all source configurations")  
            result.append("3. truffaldino_resolve_conflict_individual - Resolve each conflict individually")
            result.append("")
            result.append("After resolving conflicts, retry the sync operation.")
            
            return [types.TextContent(type="text", text="\n".join(result))]
        
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error syncing MCP servers: {str(e)}")]
    
    async def handle_show_prompts(self, app_number: int) -> List[types.TextContent]:
        """Handle show_prompts tool call"""
        try:
            app = get_app_by_number(app_number)
            if not app:
                return [types.TextContent(type="text", text=f"Invalid app number: {app_number}")]
            
            result = []
            result.append(f"System Prompt for {app.name}\n")
            
            if not app.has_prompt_support:
                result.append(f"{app.name} does not support system prompts")
                return [types.TextContent(type="text", text="\n".join(result))]
            
            prompt_data = self.config_manager.load_prompt(app_number)
            if not prompt_data:
                result.append("No system prompt found")
                return [types.TextContent(type="text", text="\n".join(result))]
            
            prompt_content, file_path = prompt_data
            result.append(f"File: {file_path}")
            result.append(f"Content ({len(prompt_content)} characters):")
            result.append("-" * 60)
            result.append(prompt_content)
            result.append("-" * 60)
            
            return [types.TextContent(type="text", text="\n".join(result))]
        
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error showing prompt: {str(e)}")]
    
    async def handle_sync_prompts(self, from_app: int, to_app: int) -> List[types.TextContent]:
        """Handle sync_prompts tool call"""
        try:
            from_app_obj = get_app_by_number(from_app)
            to_app_obj = get_app_by_number(to_app)
            
            if not from_app_obj or not to_app_obj:
                return [types.TextContent(type="text", text="Invalid app numbers")]
            
            if not from_app_obj.has_prompt_support or not to_app_obj.has_prompt_support:
                return [types.TextContent(type="text", text="One or both apps don't support system prompts")]
            
            success = self.sync_engine.sync_prompts(from_app, to_app)
            
            if success:
                result = f"[SUCCESS] Synced prompts from {from_app_obj.name} to {to_app_obj.name}"
            else:
                result = f"[FAILED] Could not sync prompts from {from_app_obj.name} to {to_app_obj.name}"
            
            return [types.TextContent(type="text", text=result)]
        
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error syncing prompts: {str(e)}")]
    
    async def handle_status(self) -> List[types.TextContent]:
        """Handle status tool call"""
        try:
            result = []
            result.append("Truffaldino System Status\n")
            
            # Check Truffaldino directories
            from config import TRUFFALDINO_DIR, VERSIONS_DIR
            
            result.append(f"Truffaldino directory: {TRUFFALDINO_DIR}")
            result.append(f"   Exists: {'YES' if TRUFFALDINO_DIR.exists() else 'NO'}")
            
            result.append(f"Versions directory: {VERSIONS_DIR}")
            if VERSIONS_DIR.exists():
                backup_count = len(list(VERSIONS_DIR.iterdir()))
                result.append(f"   Backups: {backup_count} files")
            else:
                result.append("   Exists: NO")
            
            # Check app installations
            result.append("\nDetected Applications:")
            detected_apps = self.config_manager.detect_installed_apps()
            for number, app_name, is_installed in detected_apps:
                status = "[INSTALLED]" if is_installed else "[NOT FOUND]"
                result.append(f"   {app_name}: {status}")
            
            return [types.TextContent(type="text", text="\n".join(result))]
        
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error getting status: {str(e)}")]
    
    async def handle_resolve_conflicts(self, conflicts: List[Dict[str, Any]]) -> List[types.TextContent]:
        """Handle conflict resolution via temp file editing"""
        try:
            if not conflicts:
                return [types.TextContent(type="text", text="No conflicts provided")]
            
            # Create conflict file
            conflict_file = ConflictResolver.create_conflict_file(conflicts)
            
            # Get editor command
            editor = os.environ.get('EDITOR', 'vi')
            
            result = []
            result.append("Conflict Resolution Required")
            result.append("")
            result.append(f"A conflict file has been created at: {conflict_file}")
            result.append("")
            result.append("To resolve conflicts:")
            result.append(f"1. Open the file in your editor: {editor} {conflict_file}")
            result.append("2. For each conflict, uncomment the line with your choice:")
            result.append("   - 'KEEP: source' to use the source configuration")
            result.append("   - 'KEEP: target' to use the target configuration")
            result.append("3. Save and close the file")
            result.append("4. Call this tool again to apply the resolutions")
            result.append("")
            result.append("After editing, reload this conversation and sync again.")
            
            return [types.TextContent(type="text", text="\n".join(result))]
        
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error handling conflicts: {str(e)}")]
    
    async def handle_remove_all_mcps(self, app_number: int) -> List[types.TextContent]:
        """Handle remove_all_mcps tool call"""
        try:
            app = get_app_by_number(app_number)
            if not app:
                return [types.TextContent(type="text", text=f"Invalid app number: {app_number}")]
            
            result = []
            result.append(f"Removing all MCP servers from {app.name}\n")
            
            if not app.has_mcp_support:
                result.append(f"{app.name} does not support MCP servers")
                return [types.TextContent(type="text", text="\n".join(result))]
            
            # Check current servers
            servers = self.config_manager.load_mcp_config(app_number)
            if servers is None:
                result.append(f"Failed to load configuration from {app.name}")
                return [types.TextContent(type="text", text="\n".join(result))]
            
            if not servers:
                result.append("No MCP servers found to remove")
                return [types.TextContent(type="text", text="\n".join(result))]
            
            result.append(f"Found {len(servers)} MCP servers to remove:")
            for server_name in servers.keys():
                result.append(f"  - {server_name}")
            result.append("")
            
            # Remove all servers (no confirmation in MCP mode)
            success = self.sync_engine.remove_all_mcp_servers(app_number)
            
            if success:
                result.append(f"[SUCCESS] Successfully removed all {len(servers)} MCP servers from {app.name}")
            else:
                result.append(f"[FAILED] Failed to remove MCP servers from {app.name}")
            
            return [types.TextContent(type="text", text="\n".join(result))]
        
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error removing MCP servers: {str(e)}")]
    
    async def handle_resolve_conflict_keep_target(self, from_app: int, to_app: int) -> List[types.TextContent]:
        """Handle resolving conflicts by keeping all target configurations"""
        try:
            from_app_obj = get_app_by_number(from_app)
            to_app_obj = get_app_by_number(to_app)
            
            if not from_app_obj or not to_app_obj:
                return [types.TextContent(type="text", text="Invalid app numbers")]
            
            # Load configurations
            source_servers = self.config_manager.load_mcp_config(from_app)
            target_servers = self.config_manager.load_mcp_config(to_app) or {}
            
            if source_servers is None:
                return [types.TextContent(type="text", text=f"Failed to load source configuration from {from_app_obj.name}")]
            
            # Merge by keeping target configs for conflicts, adding non-conflicting source configs
            merged = target_servers.copy()
            for server_name, source_config in source_servers.items():
                if server_name not in target_servers:
                    merged[server_name] = source_config
            
            # Save merged configuration
            success = self.config_manager.save_mcp_config(to_app, merged)
            
            if success:
                result = f"[SUCCESS] Resolved conflicts by keeping target configurations. Synced {len(merged)} MCP servers from {from_app_obj.name} to {to_app_obj.name}"
            else:
                result = f"[FAILED] Could not save resolved configuration to {to_app_obj.name}"
            
            return [types.TextContent(type="text", text=result)]
        
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error resolving conflicts: {str(e)}")]
    
    async def handle_resolve_conflict_use_source(self, from_app: int, to_app: int) -> List[types.TextContent]:
        """Handle resolving conflicts by using all source configurations"""
        try:
            from_app_obj = get_app_by_number(from_app)
            to_app_obj = get_app_by_number(to_app)
            
            if not from_app_obj or not to_app_obj:
                return [types.TextContent(type="text", text="Invalid app numbers")]
            
            # Load configurations
            source_servers = self.config_manager.load_mcp_config(from_app)
            target_servers = self.config_manager.load_mcp_config(to_app) or {}
            
            if source_servers is None:
                return [types.TextContent(type="text", text=f"Failed to load source configuration from {from_app_obj.name}")]
            
            # Merge by using source configs for conflicts, keeping non-conflicting target configs
            merged = target_servers.copy()
            for server_name, source_config in source_servers.items():
                merged[server_name] = source_config  # Always use source config
            
            # Save merged configuration
            success = self.config_manager.save_mcp_config(to_app, merged)
            
            if success:
                result = f"[SUCCESS] Resolved conflicts by using source configurations. Synced {len(merged)} MCP servers from {from_app_obj.name} to {to_app_obj.name}"
            else:
                result = f"[FAILED] Could not save resolved configuration to {to_app_obj.name}"
            
            return [types.TextContent(type="text", text=result)]
        
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error resolving conflicts: {str(e)}")]
    
    async def handle_resolve_conflict_individual(self, from_app: int, to_app: int, resolutions: Dict[str, str]) -> List[types.TextContent]:
        """Handle resolving conflicts individually based on user choices"""
        try:
            from_app_obj = get_app_by_number(from_app)
            to_app_obj = get_app_by_number(to_app)
            
            if not from_app_obj or not to_app_obj:
                return [types.TextContent(type="text", text="Invalid app numbers")]
            
            # Load configurations
            source_servers = self.config_manager.load_mcp_config(from_app)
            target_servers = self.config_manager.load_mcp_config(to_app) or {}
            
            if source_servers is None:
                return [types.TextContent(type="text", text=f"Failed to load source configuration from {from_app_obj.name}")]
            
            # Start with target configuration
            merged = target_servers.copy()
            
            # Apply individual resolutions
            resolved_count = 0
            for server_name, choice in resolutions.items():
                if server_name in source_servers:
                    if choice == "source":
                        merged[server_name] = source_servers[server_name]
                        resolved_count += 1
                    elif choice == "target":
                        # Keep existing target config (or skip if not in target)
                        if server_name not in target_servers:
                            # If not in target, we need to decide - skip it for now
                            pass
                        resolved_count += 1
            
            # Add non-conflicting source servers
            for server_name, source_config in source_servers.items():
                if server_name not in target_servers and server_name not in resolutions:
                    merged[server_name] = source_config
            
            # Save merged configuration
            success = self.config_manager.save_mcp_config(to_app, merged)
            
            if success:
                result = f"[SUCCESS] Resolved {resolved_count} conflicts individually. Synced {len(merged)} MCP servers from {from_app_obj.name} to {to_app_obj.name}"
            else:
                result = f"[FAILED] Could not save resolved configuration to {to_app_obj.name}"
            
            return [types.TextContent(type="text", text=result)]
        
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error resolving conflicts: {str(e)}")]
    
    async def run(self):
        """Run the MCP server"""
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="truffaldino",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )


async def main():
    """Main entry point for MCP server"""
    server = TruffaldinoMCPServer()
    await server.run()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
