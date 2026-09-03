#!/usr/bin/env python
"""Git MCP Server - Provides git operations as MCP tools.

This wraps git commands as MCP tool calls for AI assistants.
"""
import json
import subprocess
import sys
import os
from datetime import datetime

PROJECT_ROOT = "C:/EnvironmentPortfolio/BS_GodFile"

TOOLS = [
    {
        "name": "git_status",
        "description": "Get git status for the project",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "git_add_commit_push",
        "description": "Add all, commit with message, and push to origin",
        "inputSchema": {
            "type": "object",
            "properties": {"message": {"type": "string", "description": "Commit message"}},
            "required": []
        },
    },
    {
        "name": "git_pull",
        "description": "Pull latest changes from origin",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "git_diff",
        "description": "Show git diff for staged or unstaged changes",
        "inputSchema": {"type": "object", "properties": {"staged": {"type": "boolean"}}, "required": []},
    }
]

def git_status():
    """Get git status."""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT
    )
    return {"status": "success", "output": result.stdout}

def git_add_commit_push(message="Automated update"):
    """Add all files, commit, and push."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    full_message = f"{message} - {timestamp}"
    
    # Add
    add_result = subprocess.run(["git", "add", "."], capture_output=True, text=True, cwd=PROJECT_ROOT)
    
    # Commit
    commit_result = subprocess.run(
        ["git", "commit", "-m", full_message],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT
    )
    
    # Push
    push_result = subprocess.run(["git", "push"], capture_output=True, text=True, cwd=PROJECT_ROOT)
    
    return {
        "add": add_result.stdout + add_result.stderr,
        "commit": commit_result.stdout + commit_result.stderr,
        "push": push_result.stdout + push_result.stderr
    }

def git_pull():
    """Pull latest changes."""
    result = subprocess.run(["git", "pull"], capture_output=True, text=True, cwd=PROJECT_ROOT)
    return {"output": result.stdout + result.stderr}

def git_diff(staged=True):
    """Show diff."""
    cmd = ["git", "diff", "--staged"] if staged else ["git", "diff"]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT)
    return {"diff": result.stdout}

def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        
        rid = msg.get("id")
        method = msg.get("method", "")
        params = msg.get("params", {})
        
        if method == "initialize":
            sys.stdout.write(json.dumps({
                "jsonrpc": "2.0", "id": rid,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "git-mcp-server", "version": "1.0.0"},
                }
            }) + "\n")
            sys.stdout.flush()
        elif method == "tools/list":
            sys.stdout.write(json.dumps({
                "jsonrpc": "2.0", "id": rid,
                "result": {"tools": TOOLS}
            }) + "\n")
            sys.stdout.flush()
        elif method == "tools/call":
            tool_name = params.get("name", "")
            args = params.get("arguments", {})
            
            if tool_name == "git_status":
                result = git_status()
            elif tool_name == "git_add_commit_push":
                result = git_add_commit_push(args.get("message", "Update"))
            elif tool_name == "git_pull":
                result = git_pull()
            elif tool_name == "git_diff":
                result = git_diff(args.get("staged", True))
            else:
                result = {"status": "error", "message": f"Unknown tool: {tool_name}"}
            
            sys.stdout.write(json.dumps({
                "jsonrpc": "2.0", "id": rid,
                "result": {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}
            }) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    main()