#!/usr/bin/env python
"""AI Tool Router - Unified interface for multiple MCP-compatible AI assistants.

This script provides a single entry point for:
- OpenCode (primary, offline-capable)
- Continue.dev
- Windsurf
- Claude/Cursor

Usage:
    python ai_tool_router.py --list-tools          # List available MCP tools
    python ai_tool_router.py --tool <name> --args <json>  # Call a tool
    python ai_tool_router.py --sync-website       # Sync and deploy website
"""
import argparse
import json
import subprocess
import sys
import os

# MCP Server endpoints
MCP_SERVERS = {
    "blender": ("127.0.0.1", 9877),
    "surreal_arch": ("127.0.0.1", 9877),
}

PROJECT_ROOT = "G:\\EnvironmentPortfolio\\BS_GodFile"

def list_tools():
    """List all available MCP tools from configured servers."""
    tools = {
        "blender_mcp": [
            "blender_scene_info",
            "blender_object_info", 
            "blender_execute_code",
            "blender_viewport_screenshot",
            "blender_shared_context",
            "blender_create_handle"
        ],
        "surreal_arch_mcp": [
            "surreal_list_genomes",
            "surreal_status",
            "surreal_apply_genome",
            "surreal_randomize_dna",
            "surreal_spawn_graph",
            "surreal_smoke_test",
            "surreal_execute"
        ],
        "filesystem": [
            "read_file",
            "write_file",
            "list_files",
            "search_files"
        ],
        "agent_bridge": [
            "delegate_to_agent",
            "get_agent_status",
            "get_agent_memory",
            "run_blessing_evolution",
            "ue_editor_command"
        ]
    }
    print(json.dumps(tools, indent=2))

def sync_website():
    """Sync website to GitHub Pages deploy directory."""
    ps1_path = os.path.join(PROJECT_ROOT, "deploy", "sync_site_to_github.ps1")
    result = subprocess.run(
        ["pwsh", "-File", ps1_path],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"Error: {result.stderr}", file=sys.stderr)
    return result.returncode

def main():
    parser = argparse.ArgumentParser(description="AI Tool Router for Multi-Agent Workflow")
    parser.add_argument("--list-tools", action="store_true", help="List available MCP tools")
    parser.add_argument("--tool", help="Tool name to execute")
    parser.add_argument("--args", help="JSON arguments for tool")
    parser.add_argument("--sync-website", action="store_true", help="Sync website to GitHub Pages")
    
    args = parser.parse_args()
    
    if args.list_tools:
        list_tools()
    elif args.sync_website:
        sync_website()
    elif args.tool:
        print(f"Tool execution requires MCP client - use OpenCode or other MCP-enabled assistant")
        print(f"Tool: {args.tool}")
        print(f"Args: {args.args}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()