#!/usr/bin/env python3
"""
Truffaldino Master Management Tool
Unified interface for all Truffaldino operations
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Any
import argparse
from dotenv import load_dotenv

class TruffaldinoManager:
    """Master management interface for all Truffaldino tools"""
    
    def __init__(self):
        # Find project root
        if hasattr(sys, '_MEIPASS'):  # PyInstaller
            self.script_dir = Path(sys._MEIPASS)
        else:
            self.script_dir = Path(__file__).parent
            
        self.project_root = self.script_dir.parent
        
        # Load environment
        env_file = self.project_root / "env" / ".env"
        if env_file.exists():
            load_dotenv(env_file)
    
    def get_available_commands(self) -> Dict[str, Dict[str, Any]]:
        """Get all available Truffaldino commands"""
        commands = {
            # Core Management
            "init": {
                "script": "init.sh",
                "description": "Initialize Truffaldino system",
                "category": "setup"
            },
            "sync": {
                "script": "sync.sh", 
                "description": "Sync all configurations",
                "category": "core"
            },
            
            # Configuration Import/Export
            "import": {
                "script": "smart-import.py",
                "description": "Smart import from all detected AI tools",
                "category": "config"
            },
            "import-simple": {
                "script": "import-from-claude.py",
                "description": "Simple import from Claude Desktop",
                "category": "config"
            },
            
            # Prompt Management
            "sync-prompts": {
                "script": "sync-prompts.py",
                "description": "Sync base prompt to all AI tools",
                "category": "prompts"
            },
            
            # Version Management
            "versions": {
                "script": "manage-versions.sh",
                "description": "Manage configuration versions (list, show, diff, restore)",
                "category": "versions"
            },
            
            # Automation
            "install-agent": {
                "script": "install-launchagent.sh",
                "description": "Install LaunchAgent for auto-sync (macOS)",
                "category": "automation"
            },
            "uninstall-agent": {
                "script": "uninstall-launchagent.sh", 
                "description": "Uninstall LaunchAgent",
                "category": "automation"
            }
        }
        
        return commands
    
    def run_command(self, command: str, args: List[str] = None) -> int:
        """Execute a Truffaldino command"""
        commands = self.get_available_commands()
        
        if command not in commands:
            print(f"❌ Unknown command: {command}")
            self.show_help()
            return 1
        
        cmd_info = commands[command]
        script_path = self.script_dir / cmd_info["script"]
        
        if not script_path.exists():
            print(f"❌ Script not found: {script_path}")
            return 1
        
        # Build command arguments
        cmd_args = [str(script_path)]
        if args:
            cmd_args.extend(args)
        
        # Execute the command
        try:
            result = subprocess.run(cmd_args, cwd=self.project_root)
            return result.returncode
        except KeyboardInterrupt:
            print("\n🛑 Command interrupted")
            return 130
        except Exception as e:
            print(f"❌ Error executing command: {e}")
            return 1
    
    def show_status(self) -> None:
        """Show current Truffaldino system status"""
        print("🎪 Truffaldino System Status")
        print("=" * 50)
        
        # Check environment file
        env_file = self.project_root / "env" / ".env"
        if env_file.exists():
            print("✅ Environment file: Found")
            base_prompt = os.environ.get("BASE_PROMPT")
            if base_prompt:
                print(f"📄 Base prompt: {base_prompt}")
                if Path(base_prompt).exists():
                    print("   Status: ✅ Found")
                else:
                    print("   Status: ❌ File not found")
            else:
                print("📄 Base prompt: Not configured")
        else:
            print("❌ Environment file: Missing (.env)")
        
        # Check master config
        master_config = self.project_root / "configs" / "master-config.yaml"
        if master_config.exists():
            print("✅ Master config: Found")
        else:
            print("❌ Master config: Missing")
        
        # Check LaunchAgent (macOS only)
        if sys.platform == "darwin":
            try:
                result = subprocess.run(
                    ["launchctl", "list"], 
                    capture_output=True, 
                    text=True, 
                    timeout=5
                )
                if "com.truffaldino.autosync" in result.stdout:
                    print("✅ LaunchAgent: Active")
                else:
                    print("⏸️  LaunchAgent: Not installed")
            except:
                print("❓ LaunchAgent: Status unknown")
        
        # Check version directory
        version_dir = Path.home() / ".truffaldino" / "versions"
        if version_dir.exists():
            version_count = len(list(version_dir.iterdir()))
            print(f"📚 Versions: {version_count} backups stored")
        else:
            print("📚 Versions: No backups yet")
        
        print()
    
    def show_help(self) -> None:
        """Show help information"""
        print("🎪 Truffaldino - AI Development Configuration Manager")
        print()
        print("Usage: truffaldino <command> [arguments...]")
        print()
        
        commands = self.get_available_commands()
        categories = {}
        
        # Group commands by category
        for cmd_name, cmd_info in commands.items():
            category = cmd_info["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append((cmd_name, cmd_info["description"]))
        
        # Display commands by category
        category_names = {
            "setup": "🚀 Setup & Initialization",
            "core": "⚙️  Core Operations", 
            "config": "📋 Configuration Management",
            "prompts": "💬 Prompt Management",
            "versions": "📚 Version Control",
            "automation": "🤖 Automation"
        }
        
        for category, title in category_names.items():
            if category in categories:
                print(f"{title}:")
                for cmd_name, description in categories[category]:
                    print(f"  {cmd_name:15} {description}")
                print()
        
        print("Special Commands:")
        print(f"  {'status':15} Show system status")
        print(f"  {'help':15} Show this help message")
        print()
        
        print("Examples:")
        print("  truffaldino init              # Initialize the system")
        print("  truffaldino import            # Smart import from all tools") 
        print("  truffaldino sync              # Sync all configurations")
        print("  truffaldino sync-prompts      # Sync base prompt to all tools")
        print("  truffaldino versions list     # List configuration versions")
        print("  truffaldino status            # Show system status")
        print()
    
    def interactive_mode(self) -> None:
        """Run in interactive mode"""
        print("🎪 Truffaldino Interactive Mode")
        print("Type 'help' for commands, 'exit' to quit")
        print()
        
        while True:
            try:
                user_input = input("truffaldino> ").strip()
                if not user_input:
                    continue
                    
                if user_input.lower() in ["exit", "quit", "q"]:
                    print("👋 Goodbye!")
                    break
                    
                parts = user_input.split()
                command = parts[0]
                args = parts[1:] if len(parts) > 1 else []
                
                if command == "help":
                    self.show_help()
                elif command == "status":
                    self.show_status()
                else:
                    self.run_command(command, args)
                    
                print()  # Add spacing between commands
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except EOFError:
                print("\n👋 Goodbye!")
                break

def main():
    parser = argparse.ArgumentParser(
        description="Truffaldino - AI Development Configuration Manager",
        add_help=False  # We'll handle help ourselves
    )
    parser.add_argument("command", nargs="?", help="Command to execute")
    parser.add_argument("args", nargs="*", help="Command arguments")
    parser.add_argument("-i", "--interactive", action="store_true", help="Run in interactive mode")
    
    # Parse known args to handle our custom help
    args, unknown = parser.parse_known_args()
    
    manager = TruffaldinoManager()
    
    # Handle special cases
    if args.interactive:
        manager.interactive_mode()
        return 0
    
    if not args.command or args.command in ["help", "-h", "--help"]:
        manager.show_help()
        return 0
        
    if args.command == "status":
        manager.show_status()
        return 0
    
    # Combine parsed and unknown args for the command
    all_args = args.args + unknown
    
    return manager.run_command(args.command, all_args)

if __name__ == "__main__":
    sys.exit(main())