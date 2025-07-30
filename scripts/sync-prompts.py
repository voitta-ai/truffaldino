#!/usr/bin/env python3
"""
Truffaldino Prompt Synchronization
Propagates base prompt to different AI assistants
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
import argparse
from dotenv import load_dotenv

class PromptSync:
    """Synchronize base prompt across different AI tools"""
    
    # Target locations for different AI tools
    PROMPT_TARGETS = {
        "claude_code": {
            "path": Path.home() / ".claude" / "system_prompt.md",
            "format": "markdown",
            "description": "Claude Code system prompt"
        },
        "cline": {
            "path": Path.home() / ".cline" / "system_prompt.md",
            "format": "markdown", 
            "description": "Cline system prompt"
        },
        "cursor": {
            "path": Path.home() / ".cursor" / "system_prompt.md",
            "format": "markdown",
            "description": "Cursor system prompt"
        },
        "windsurf": {
            "path": Path.home() / ".windsurf" / "system_prompt.md", 
            "format": "markdown",
            "description": "Windsurf system prompt"
        },
        "jetbrains": {
            "path": Path.home() / "Library/Application Support/JetBrains/IntelliJIdea2024.3/options/ai_assistant_system_prompt.txt",
            "format": "text",
            "description": "JetBrains AI Assistant system prompt"
        },
        "continue": {
            "path": Path.home() / ".continue" / "system_prompt.md",
            "format": "markdown",
            "description": "Continue.dev system prompt"
        }
    }
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.version_dir = Path.home() / ".truffaldino" / "versions" / "prompts"
        self.version_dir.mkdir(parents=True, exist_ok=True)
        
        # Load environment variables
        env_file = project_root / "env" / ".env"
        if env_file.exists():
            load_dotenv(env_file)
            
        self.base_prompt_path = self._get_base_prompt_path()
        
    def _get_base_prompt_path(self) -> Optional[Path]:
        """Get base prompt path from environment or default"""
        base_prompt = os.environ.get("BASE_PROMPT")
        if base_prompt:
            path = Path(base_prompt).expanduser()
            if path.exists():
                return path
            else:
                print(f"⚠️  BASE_PROMPT path doesn't exist: {base_prompt}")
        
        # Try default locations
        default_locations = [
            self.project_root / "prompts" / "base-prompt.md",
            Path.home() / "base-prompt.md",
            Path("/Users/gregory.golberg/g/svalka/llm/base-prompt.md")  # User's current setup
        ]
        
        for location in default_locations:
            if location.exists():
                return location
                
        return None
    
    def load_base_prompt(self) -> Optional[str]:
        """Load the base prompt content"""
        if not self.base_prompt_path:
            print("❌ No base prompt found. Please set BASE_PROMPT in .env or create prompts/base-prompt.md")
            return None
            
        try:
            with open(self.base_prompt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except Exception as e:
            print(f"❌ Error reading base prompt: {e}")
            return None
    
    def detect_available_tools(self) -> Dict[str, Dict[str, Any]]:
        """Detect which AI tools are available on the system"""
        available = {}
        
        for tool_name, config in self.PROMPT_TARGETS.items():
            target_path = config["path"]
            
            # Check if the parent directory exists (tool is likely installed)
            if target_path.parent.exists():
                available[tool_name] = {
                    **config,
                    "exists": target_path.exists(),
                    "writable": os.access(target_path.parent, os.W_OK)
                }
                
        return available
    
    def backup_existing_prompt(self, tool_name: str, target_path: Path) -> Optional[str]:
        """Create a backup of existing prompt"""
        if not target_path.exists():
            return None
            
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{tool_name}_system_prompt_{timestamp}"
        backup_path = self.version_dir / backup_name
        
        try:
            shutil.copy2(target_path, backup_path)
            return str(backup_path)
        except Exception as e:
            print(f"⚠️  Could not backup {tool_name} prompt: {e}")
            return None
    
    def sync_to_tool(self, tool_name: str, content: str, config: Dict[str, Any]) -> bool:
        """Sync prompt content to a specific tool"""
        target_path = config["path"]
        
        # Create parent directory if it doesn't exist
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Backup existing prompt
        if target_path.exists():
            backup_path = self.backup_existing_prompt(tool_name, target_path)
            if backup_path:
                print(f"  💾 Backed up existing prompt to versions/")
        
        try:
            # Format content based on tool requirements
            formatted_content = self.format_prompt_for_tool(content, config["format"])
            
            # Write the new prompt
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(formatted_content)
                
            print(f"  ✅ Synced to {config['description']}")
            print(f"     {target_path}")
            return True
            
        except Exception as e:
            print(f"  ❌ Failed to sync to {tool_name}: {e}")
            return False
    
    def format_prompt_for_tool(self, content: str, format_type: str) -> str:
        """Format prompt content for specific tool requirements"""
        if format_type == "text":
            # Strip markdown formatting for plain text tools
            import re
            # Remove markdown headers
            content = re.sub(r'^#+\s+', '', content, flags=re.MULTILINE)
            # Remove markdown emphasis
            content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)
            content = re.sub(r'\*(.*?)\*', r'\1', content)
            # Remove code blocks
            content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
            content = re.sub(r'`(.*?)`', r'\1', content)
            
        return content
    
    def sync_all(self, tools: Optional[list] = None, dry_run: bool = False) -> None:
        """Sync base prompt to all or specified tools"""
        print("🔄 Truffaldino Prompt Sync")
        print("=" * 40)
        
        # Load base prompt
        base_content = self.load_base_prompt()
        if not base_content:
            return
            
        print(f"📖 Base prompt: {self.base_prompt_path}")
        print(f"   Size: {len(base_content)} characters")
        print()
        
        # Detect available tools
        available_tools = self.detect_available_tools()
        
        if not available_tools:
            print("❌ No AI tools detected on this system")
            return
        
        print("🔍 Detected AI tools:")
        for tool_name, config in available_tools.items():
            status = "✅ exists" if config["exists"] else "➕ will create"
            writable = "✏️  writable" if config["writable"] else "🔒 read-only"
            print(f"  • {tool_name:12} {status}, {writable}")
            print(f"    {config['description']}")
        print()
        
        # Filter tools if specified
        if tools:
            available_tools = {k: v for k, v in available_tools.items() if k in tools}
            if not available_tools:
                print(f"❌ None of the specified tools are available: {', '.join(tools)}")
                return
        
        if dry_run:
            print("🏃 Dry run mode - no files will be modified")
            return
        
        # Sync to each tool
        print("📝 Syncing prompts:")
        success_count = 0
        
        for tool_name, config in available_tools.items():
            if not config["writable"]:
                print(f"  ⏭️  Skipping {tool_name} (not writable)")
                continue
                
            print(f"  🔄 {tool_name}...")
            if self.sync_to_tool(tool_name, base_content, config):
                success_count += 1
        
        print()
        print(f"🎉 Sync complete! Updated {success_count}/{len(available_tools)} tools")
        
        if success_count < len(available_tools):
            print("💡 Tip: Some tools may require restart to pick up new prompts")

def main():
    parser = argparse.ArgumentParser(description="Sync base prompt across AI tools")
    parser.add_argument("--tools", nargs="+", help="Specific tools to sync to")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    parser.add_argument("--list", action="store_true", help="List available tools and exit")
    args = parser.parse_args()
    
    # Find project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    sync = PromptSync(project_root)
    
    if args.list:
        print("🔍 Available AI tools:")
        available_tools = sync.detect_available_tools()
        for tool_name, config in available_tools.items():
            status = "installed" if config["exists"] else "not found"
            print(f"  • {tool_name:12} {status}")
            print(f"    {config['description']}")
            print(f"    {config['path']}")
        return
    
    sync.sync_all(args.tools, args.dry_run)

if __name__ == "__main__":
    main()