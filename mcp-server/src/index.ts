#!/usr/bin/env node

/**
 * Truffaldino MCP Server
 * Provides access to Truffaldino configuration management tools via MCP
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
  CallToolResult,
} from "@modelcontextprotocol/sdk/types.js";
import { execSync } from "child_process";
import { readFileSync, existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Find the project root (go up from mcp-server/dist or mcp-server/src to project root)
const PROJECT_ROOT = join(__dirname, "..", "..");
const SCRIPTS_DIR = join(PROJECT_ROOT, "scripts");

interface TruffaldinoTool {
  name: string;
  description: string;
  script: string;
  category: string;
  examples?: string[];
  parameters?: {
    type: "object";
    properties: Record<string, any>;
    required?: string[];
  };
}

const TRUFFALDINO_TOOLS: TruffaldinoTool[] = [
  {
    name: "truffaldino_status",
    description: "Show current Truffaldino system status and configuration health",
    script: "truffaldino.py",
    category: "core",
    examples: ["Check if all configurations are properly set up"],
    parameters: {
      type: "object", 
      properties: {},
      required: []
    }
  },
  {
    name: "truffaldino_sync",
    description: "Sync all configurations across AI tools (Claude Desktop, Claude Code, Cline, etc.)",
    script: "sync.sh",
    category: "core",
    examples: ["After adding a new MCP server", "When switching between projects"],
    parameters: {
      type: "object",
      properties: {},
      required: []
    }
  },
  {
    name: "truffaldino_import",
    description: "Smart import configurations from all detected AI tools with conflict resolution",
    script: "smart-import.py", 
    category: "config",
    examples: ["Set up Truffaldino from existing configs", "Merge configs from multiple tools"],
    parameters: {
      type: "object",
      properties: {},
      required: []
    }
  },
  {
    name: "truffaldino_sync_prompts",
    description: "Sync base system prompt to all AI tools",
    script: "sync-prompts.py",
    category: "prompts",
    examples: ["After updating your base prompt", "Setting up consistent prompts across tools"],
    parameters: {
      type: "object",
      properties: {
        tools: {
          type: "array",
          items: { type: "string" },
          description: "Specific tools to sync to (optional)"
        },
        dry_run: {
          type: "boolean",
          description: "Show what would be done without making changes"
        }
      },
      required: []
    }
  },
  {
    name: "truffaldino_list_versions",
    description: "List available versions/backups of configuration files",
    script: "manage-versions.sh",
    category: "versions",
    examples: ["Before making major changes", "To see backup history"],
    parameters: {
      type: "object",
      properties: {
        file: {
          type: "string",
          description: "Specific file to list versions for (optional)"
        }
      },
      required: []
    }
  },
  {
    name: "truffaldino_restore_version",
    description: "Restore a configuration file to a previous version",
    script: "manage-versions.sh",
    category: "versions",
    examples: ["After a bad configuration change", "Rolling back to working state"],
    parameters: {
      type: "object",
      properties: {
        file: {
          type: "string", 
          description: "Configuration file name to restore"
        },
        version: {
          type: "string",
          description: "Version timestamp to restore to"
        }
      },
      required: ["file", "version"]
    }
  },
  {
    name: "truffaldino_install_automation",
    description: "Install LaunchAgent for automatic configuration sync (macOS only)",
    script: "install-launchagent.sh",
    category: "automation",
    examples: ["Set up automatic sync when configs change"],
    parameters: {
      type: "object",
      properties: {},
      required: []
    }
  },
  {
    name: "truffaldino_help",
    description: "Show detailed help and available commands",
    script: "truffaldino.py",
    category: "help",
    examples: ["Learn about available commands", "Get usage examples"],
    parameters: {
      type: "object",
      properties: {},
      required: []
    }
  }
];

class TruffaldinoMCPServer {
  private server: Server;

  constructor() {
    this.server = new Server(
      {
        name: "truffaldino-mcp-server",
        version: "1.0.0",
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupHandlers();
  }

  private setupHandlers() {
    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: TRUFFALDINO_TOOLS.map((tool): Tool => ({
          name: tool.name,
          description: tool.description,
          inputSchema: tool.parameters || {
            type: "object",
            properties: {},
            required: []
          }
        }))
      };
    });

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;
      
      const tool = TRUFFALDINO_TOOLS.find(t => t.name === name);
      if (!tool) {
        return {
          content: [
            {
              type: "text",
              text: `Unknown tool: ${name}`
            }
          ]
        };
      }

      return this.executeTool(tool, args || {});
    });
  }

  private async executeTool(tool: TruffaldinoTool, args: Record<string, any>): Promise<CallToolResult> {
    try {
      const scriptPath = join(SCRIPTS_DIR, tool.script);
      
      if (!existsSync(scriptPath)) {
        return {
          content: [
            {
              type: "text", 
              text: `Script not found: ${scriptPath}`
            }
          ]
        };
      }

      // Build command based on tool and arguments
      let command = this.buildCommand(tool, args, scriptPath);
      
      // Execute the command
      const output = execSync(command, {
        cwd: PROJECT_ROOT,
        encoding: "utf-8",
        timeout: 60000, // 60 second timeout
        env: {
          ...process.env,
          PATH: process.env.PATH + ":/usr/local/bin:/opt/homebrew/bin"
        }
      });

      return {
        content: [
          {
            type: "text",
            text: `✅ ${tool.name} completed successfully:\n\n${output}`
          }
        ]
      };

    } catch (error: any) {
      const errorMsg = error.stdout || error.stderr || error.message || "Unknown error";
      
      return {
        content: [
          {
            type: "text",
            text: `❌ ${tool.name} failed:\n\n${errorMsg}`
          }
        ]
      };
    }
  }

  private buildCommand(tool: TruffaldinoTool, args: Record<string, any>, scriptPath: string): string {
    let command = scriptPath;

    // Handle specific tools with special argument patterns
    switch (tool.name) {
      case "truffaldino_status":
        command = `${scriptPath} status`;
        break;
        
      case "truffaldino_help":
        command = `${scriptPath} help`;
        break;
        
      case "truffaldino_sync_prompts":
        if (args.tools && Array.isArray(args.tools)) {
          command += ` --tools ${args.tools.join(" ")}`;
        }
        if (args.dry_run) {
          command += " --dry-run";
        }
        break;
        
      case "truffaldino_list_versions":
        command += " list";
        if (args.file) {
          command += ` "${args.file}"`;
        }
        break;
        
      case "truffaldino_restore_version":
        if (args.file && args.version) {
          command += ` restore "${args.file}" "${args.version}"`;
        } else {
          throw new Error("Both 'file' and 'version' parameters are required for restore");
        }
        break;
    }

    return command;
  }

  async start() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error("Truffaldino MCP server running on stdio");
  }
}

// Start the server
const server = new TruffaldinoMCPServer();
server.start().catch((error) => {
  console.error("Failed to start server:", error);
  process.exit(1);
});