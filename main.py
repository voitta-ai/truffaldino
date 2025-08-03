#!/usr/bin/env python3
"""
Truffaldino - AI Development Configuration Manager
Main CLI interface
"""

import sys
import argparse
import json
from typing import Optional

from config import SUPPORTED_APPS, get_app_by_number
from sync import ConfigManager, SyncEngine


class TruffaldinoApp:
    """Main application class"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.sync_engine = SyncEngine()
    
    def run_cli(self, args: argparse.Namespace) -> int:
        """Run CLI with parsed arguments"""
        
        if args.list_apps:
            return self.list_apps()
        
        elif args.show_mcps:
            return self.show_mcps(args.show_mcps)
        
        elif args.show_prompt:
            return self.show_prompt(args.show_prompt)
        
        elif args.sync_mcp:
            if not args.from_app or not args.to_app:
                print("Error: --sync-mcp requires both --from and --to flags")
                return 1
            return self.sync_mcps(args.from_app, args.to_app)
        
        elif args.sync_prompt:
            if not args.from_app or not args.to_app:
                print("Error: --sync-prompt requires both --from and --to flags")
                return 1
            return self.sync_prompts(args.from_app, args.to_app)
        
        elif args.remove_all_mcps:
            return self.remove_all_mcps(args.remove_all_mcps)
        
        else:
            # No flags provided, run interactive mode
            return self.interactive_mode()
    
    def list_apps(self) -> int:
        """List all supported applications"""
        print("Truffaldino - Supported AI Applications\n")
        
        detected_apps = self.config_manager.detect_installed_apps()
        
        for number, app_name, is_installed in detected_apps:
            status = "[INSTALLED]" if is_installed else "[NOT FOUND]"
            print(f"{number}. {app_name:15} {status}")
        
        return 0
    
    def show_mcps(self, app_number: int) -> int:
        """Show MCP servers for a specific app"""
        app = get_app_by_number(app_number)
        if not app:
            print(f"Error: Invalid app number {app_number}")
            return 1
        
        print(f"MCP Servers for {app.name}\n")
        
        if not app.has_mcp_support:
            print(f"{app.name} does not support MCP servers")
            return 0
        
        servers = self.config_manager.load_mcp_config(app_number)
        if servers is None:
            print(f"Failed to load configuration from {app.name}")
            return 1
        
        if not servers:
            print("No MCP servers configured")
            return 0
        
        for server_name, config in servers.items():
            print(f"* {server_name}")
            print(f"   Command: {config.get('command', 'N/A')}")
            if config.get('args'):
                print(f"   Args: {' '.join(config['args'])}")
            if config.get('env'):
                print(f"   Environment: {list(config['env'].keys())}")
            print()
        
        print(f"Total: {len(servers)} MCP servers")
        return 0
    
    def show_prompt(self, app_number: int) -> int:
        """Show prompt for a specific app"""
        app = get_app_by_number(app_number)
        if not app:
            print(f"Error: Invalid app number {app_number}")
            return 1
        
        print(f"System Prompt for {app.name}\n")
        
        if not app.has_prompt_support:
            print(f"{app.name} does not support system prompts")
            return 0
        
        prompt_data = self.config_manager.load_prompt(app_number)
        if not prompt_data:
            print("No system prompt found")
            return 0
        
        prompt_content, file_path = prompt_data
        print(f"File: {file_path}")
        print(f"Content ({len(prompt_content)} characters):")
        print("-" * 60)
        print(prompt_content)
        print("-" * 60)
        
        return 0
    
    def sync_mcps(self, from_app: int, to_app: int) -> int:
        """Sync MCP servers between apps"""
        from_app_obj = get_app_by_number(from_app)
        to_app_obj = get_app_by_number(to_app)
        
        if not from_app_obj or not to_app_obj:
            print("Error: Invalid app numbers")
            return 1
        
        print(f"Syncing MCP servers: {from_app_obj.name} -> {to_app_obj.name}\n")
        
        if not from_app_obj.has_mcp_support or not to_app_obj.has_mcp_support:
            print("Error: One or both apps don't support MCP servers")
            return 1
        
        success = self.sync_engine.sync_mcp_servers(from_app, to_app, mode="smart")
        return 0 if success else 1
    
    def sync_prompts(self, from_app: int, to_app: int) -> int:
        """Sync prompts between apps"""
        from_app_obj = get_app_by_number(from_app)
        to_app_obj = get_app_by_number(to_app)
        
        if not from_app_obj or not to_app_obj:
            print("Error: Invalid app numbers")
            return 1
        
        print(f"Syncing prompts: {from_app_obj.name} -> {to_app_obj.name}\n")
        
        if not from_app_obj.has_prompt_support or not to_app_obj.has_prompt_support:
            print("Error: One or both apps don't support system prompts")
            return 1
        
        success = self.sync_engine.sync_prompts(from_app, to_app)
        return 0 if success else 1
    
    def remove_all_mcps(self, app_number: int) -> int:
        """Remove all MCP servers from a specific app"""
        app = get_app_by_number(app_number)
        if not app:
            print(f"Error: Invalid app number {app_number}")
            return 1
        
        print(f"Removing all MCP servers from {app.name}\n")
        
        if not app.has_mcp_support:
            print(f"{app.name} does not support MCP servers")
            return 0
        
        # Check current servers
        servers = self.config_manager.load_mcp_config(app_number)
        if servers is None:
            print(f"Failed to load configuration from {app.name}")
            return 1
        
        if not servers:
            print("No MCP servers found to remove")
            return 0
        
        print(f"Found {len(servers)} MCP servers:")
        for server_name in servers.keys():
            print(f"  - {server_name}")
        
        # Confirm removal
        confirm = input(f"\nAre you sure you want to remove all {len(servers)} MCP servers from {app.name}? (y/N): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("Operation cancelled")
            return 0
        
        # Remove all servers
        success = self.sync_engine.remove_all_mcp_servers(app_number)
        if success:
            print(f"[SUCCESS] Successfully removed all MCP servers from {app.name}")
            return 0
        else:
            print(f"[FAILED] Failed to remove MCP servers from {app.name}")
            return 1
    
    def interactive_mode(self) -> int:
        """Run interactive text menu"""
        while True:
            self.show_menu()
            choice = input("\nChoice: ").strip().lower()
            
            if choice == 'f' or choice == 'exit':
                print("Goodbye!")
                return 0
            
            elif choice == 'a':
                self.interactive_show_mcps()
            
            elif choice == 'b':
                self.interactive_sync_mcps()
            
            elif choice == 'c':
                self.interactive_sync_prompts()
            
            elif choice == 'd':
                self.interactive_remove_all_mcps()
            
            elif choice == 'e':
                self.show_system_status()
            
            else:
                print("Invalid choice. Please try again.")
            
            input("\nPress Enter to continue...")
    
    def show_menu(self):
        """Display the interactive menu"""
        print("\n" + "="*60)
        print("Truffaldino - AI Development Configuration Manager")
        print("="*60)
        
        print("\nAvailable AI Applications:")
        detected_apps = self.config_manager.detect_installed_apps()
        for number, app_name, is_installed in detected_apps:
            status = "[INSTALLED]" if is_installed else "[NOT FOUND]"
            print(f"{number}. {status} {app_name}")
        
        print("\nOptions:")
        print("a) List/Show MCP servers for an app")
        print("b) Sync MCP servers between apps")
        print("c) Show/Sync prompts between apps")
        print("d) Remove all MCP servers from an app")
        print("e) Show system status")
        print("f) Exit")
    
    def interactive_show_mcps(self):
        """Interactive MCP server listing"""
        print("\nShow MCP Servers")
        print("-" * 30)
        
        app_number = self.get_app_choice("Which app to show MCP servers for")
        if app_number:
            self.show_mcps(app_number)
    
    def interactive_sync_mcps(self):
        """Interactive MCP server syncing"""
        print("\nSync MCP Servers")
        print("-" * 30)
        
        from_app = self.get_app_choice("Source app (copy FROM)")
        if not from_app:
            return
        
        to_app = self.get_app_choice("Target app (copy TO)")
        if not to_app:
            return
        
        if from_app == to_app:
            print("Error: Source and target must be different")
            return
        
        self.sync_mcps(from_app, to_app)
    
    def interactive_sync_prompts(self):
        """Interactive prompt syncing"""
        print("\nSync Prompts")
        print("-" * 30)
        
        # First show which apps support prompts
        prompt_apps = [(i+1, app) for i, app in enumerate(SUPPORTED_APPS) if app.has_prompt_support]
        if not prompt_apps:
            print("No apps support system prompts")
            return
        
        print("Apps with prompt support:")
        for number, app in prompt_apps:
            print(f"{number}. {app.name}")
        
        from_app = self.get_app_choice("Source app (copy FROM)", prompt_only=True)
        if not from_app:
            return
        
        to_app = self.get_app_choice("Target app (copy TO)", prompt_only=True)
        if not to_app:
            return
        
        if from_app == to_app:
            print("Error: Source and target must be different")
            return
        
        self.sync_prompts(from_app, to_app)
    
    def interactive_remove_all_mcps(self):
        """Interactive MCP server removal"""
        print("\nRemove All MCP Servers")
        print("-" * 30)
        
        app_number = self.get_app_choice("Which app to remove all MCP servers from")
        if app_number:
            self.remove_all_mcps(app_number)
    
    def get_app_choice(self, prompt_text: str, prompt_only: bool = False) -> Optional[int]:
        """Get app choice from user"""
        try:
            choice = input(f"{prompt_text} (number): ").strip()
            app_number = int(choice)
            
            app = get_app_by_number(app_number)
            if not app:
                print(f"Invalid app number: {app_number}")
                return None
            
            if prompt_only and not app.has_prompt_support:
                print(f"{app.name} does not support prompts")
                return None
            
            return app_number
        except ValueError:
            print("Please enter a valid number")
            return None
    
    def show_system_status(self):
        """Show system status"""
        print("\nSystem Status")
        print("-" * 30)
        
        # Check Truffaldino directories
        from config import TRUFFALDINO_DIR, VERSIONS_DIR
        
        print(f"Truffaldino directory: {TRUFFALDINO_DIR}")
        print(f"   Exists: {'YES' if TRUFFALDINO_DIR.exists() else 'NO'}")
        
        print(f"Versions directory: {VERSIONS_DIR}")
        if VERSIONS_DIR.exists():
            backup_count = len(list(VERSIONS_DIR.iterdir()))
            print(f"   Backups: {backup_count} files")
        else:
            print("   Exists: NO")
        
        # Check app installations
        print("\nDetected Applications:")
        detected_apps = self.config_manager.detect_installed_apps()
        for number, app_name, is_installed in detected_apps:
            status = "[INSTALLED]" if is_installed else "[NOT FOUND]"
            print(f"   {app_name}: {status}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Truffaldino - AI Development Configuration Manager",
        epilog="Run without arguments for interactive mode"
    )
    
    parser.add_argument("--list-apps", action="store_true",
                       help="List supported AI apps")
    parser.add_argument("--show-mcps", type=int, metavar="N",
                       help="Show MCP servers for app number N")
    parser.add_argument("--show-prompt", type=int, metavar="N",
                       help="Show system prompt for app number N")
    parser.add_argument("--sync-mcp", action="store_true",
                       help="Sync MCP servers between apps (requires --from and --to)")
    parser.add_argument("--sync-prompt", action="store_true",
                       help="Sync prompts between apps (requires --from and --to)")
    parser.add_argument("--from", dest="from_app", type=int, metavar="N",
                       help="Source app number for sync operations")
    parser.add_argument("--to", dest="to_app", type=int, metavar="N",
                       help="Target app number for sync operations")
    parser.add_argument("--remove-all-mcps", type=int, metavar="N",
                       help="Remove all MCP servers from app number N")
    
    args = parser.parse_args()
    
    app = TruffaldinoApp()
    return app.run_cli(args)


if __name__ == "__main__":
    sys.exit(main())
