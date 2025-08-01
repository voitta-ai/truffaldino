"""
Truffaldino Configuration Module
Defines supported AI applications and their configuration paths
"""

import os
import platform
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class AIApp:
    """Represents an AI application configuration"""
    id: str
    name: str
    config_paths: Dict[str, Path] = field(default_factory=dict)
    config_format: str = "json"
    prompt_paths: Dict[str, Path] = field(default_factory=dict)
    prompt_format: str = "text"
    has_mcp_support: bool = True
    has_prompt_support: bool = False
    
    def get_config_path(self) -> Optional[Path]:
        """Get the configuration path for current platform"""
        system = platform.system()
        if system == "Darwin":
            return self.config_paths.get("macos")
        elif system == "Linux":
            return self.config_paths.get("linux")
        elif system == "Windows":
            return self.config_paths.get("windows")
        return None
    
    def get_prompt_path(self) -> Optional[Path]:
        """Get the prompt path for current platform"""
        system = platform.system()
        if system == "Darwin":
            return self.prompt_paths.get("macos")
        elif system == "Linux":
            return self.prompt_paths.get("linux")
        elif system == "Windows":
            return self.prompt_paths.get("windows")
        return None


# Define supported AI applications
SUPPORTED_APPS = [
    AIApp(
        id="claude_desktop",
        name="Claude Desktop",
        config_paths={
            "macos": Path.home() / "Library/Application Support/Claude/claude_desktop_config.json",
            "linux": Path.home() / ".config/claude/config.json",
            "windows": Path.home() / "AppData/Roaming/Claude/config.json",
        },
        config_format="json",
        has_mcp_support=True,
        has_prompt_support=False
    ),
    AIApp(
        id="claude_code",
        name="Claude Code",
        # Claude Code uses CLI commands, no config file
        config_paths={},
        config_format="cli",
        has_mcp_support=True,
        has_prompt_support=False
    ),
    AIApp(
        id="cline",
        name="Cline",
        config_paths={
            "macos": Path.home() / ".cline/mcp_settings.json",
            "linux": Path.home() / ".cline/mcp_settings.json",
            "windows": Path.home() / ".cline/mcp_settings.json",
        },
        config_format="json",
        has_mcp_support=True,
        has_prompt_support=True,
        prompt_paths={
            "macos": Path.home() / ".cline/system_prompt.txt",
            "linux": Path.home() / ".cline/system_prompt.txt",
            "windows": Path.home() / ".cline/system_prompt.txt",
        }
    ),
    AIApp(
        id="cursor",
        name="Cursor",
        config_paths={
            "macos": Path.home() / ".cursor/mcp_config.json",
            "linux": Path.home() / ".cursor/mcp_config.json",
            "windows": Path.home() / ".cursor/mcp_config.json",
        },
        config_format="json",
        has_mcp_support=True,
        has_prompt_support=True,
        prompt_paths={
            "macos": Path.home() / ".cursor/system_prompt.txt",
            "linux": Path.home() / ".cursor/system_prompt.txt",
            "windows": Path.home() / ".cursor/system_prompt.txt",
        }
    ),
    AIApp(
        id="intellij",
        name="IntelliJ",
        config_paths={
            "macos": Path.home() / "Library/Application Support/JetBrains",
            "linux": Path.home() / ".config/JetBrains",
            "windows": Path.home() / "AppData/Roaming/JetBrains",
        },
        config_format="xml",
        has_mcp_support=True,
        has_prompt_support=True,
        prompt_format="text"
    )
]


def get_app_by_id(app_id: str) -> Optional[AIApp]:
    """Get an AI application by its ID"""
    for app in SUPPORTED_APPS:
        if app.id == app_id:
            return app
    return None


def get_app_by_number(number: int) -> Optional[AIApp]:
    """Get an AI application by its number (1-based)"""
    if 1 <= number <= len(SUPPORTED_APPS):
        return SUPPORTED_APPS[number - 1]
    return None


def list_apps() -> List[Tuple[int, AIApp]]:
    """List all supported applications with numbers"""
    return [(i + 1, app) for i, app in enumerate(SUPPORTED_APPS)]


# Truffaldino configuration directory
TRUFFALDINO_DIR = Path.home() / ".truffaldino"
VERSIONS_DIR = TRUFFALDINO_DIR / "versions"
CONFLICTS_LOG = TRUFFALDINO_DIR / "conflicts.log"
CONFIG_FILE = TRUFFALDINO_DIR / "config.json"

# Version control settings
MAX_VERSIONS_PER_APP = 10

# Conflict resolution settings
TEMP_CONFLICT_FILE = "/tmp/truffaldino_conflict.txt"