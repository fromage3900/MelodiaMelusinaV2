#!/usr/bin/env python3
"""mcp_compile_feedback_server.py

MCP server exposing the `cpp_compile_and_feedback` tool to AI agents.

Purpose:
    Make the compile-feedback loop available to any MCP-capable agent (Claude,
    DeepSeek, Kimi, etc.) so the agent can invoke the build and receive
    structured JSON errors without a human orchestrating the rebuild gate.

Usage:
    python mcp_compile_feedback_server.py          # stdio transport (default)
    python mcp_compile_feedback_server.py --help

Design:
    - Uses the official MCP Python SDK (mcp) with stdio transport (matches the
      ueblueprintmcp pattern in .mcp.json).
    - Exposes one tool: `cpp_compile_and_feedback`.
    - The tool calls the CLI (`cpp_compile_and_feedback.py`) and returns the
      structured JSON result directly.

Register in BS_GodFile/.mcp.json:
    "cpp-compile-feedback": {
      "command": "C:/EnvironmentPortfolio/BS_GodFile/Content/Python/venv/Scripts/python.exe",
      "args": ["C:/EnvironmentPortfolio/BS_GodFile/Content/Python/mcp_compile_feedback_server.py"],
      "env": {
        "MELODIA_PROJECT_ROOT": "C:/EnvironmentPortfolio/BS_GodFile"
      }
    }
"""

import argparse
import json
import os
import subprocess
import sys

from mcp.server.fastmcp import FastMCP

# Create an MCP server instance
mcp = FastMCP("cpp-compile-feedback")

# Path to the CLI tool
CLI_PATH = os.path.join(os.path.dirname(__file__), "cpp_compile_and_feedback.py")


@mcp.tool()
def cpp_compile_and_feedback(
    live_coding: bool = False,
    dry_run: bool = False,
    target: str = "Editor",
) -> str:
    """Compile the C++ project and return structured feedback.

    Args:
        live_coding: Use Live Coding path (requires editor open). Default False.
        dry_run: Print the command without running it. Default False.
        target: Build target name (e.g. Editor, Game). Default "Editor".

    Returns:
        JSON string with the compile result:
        {
          "success": bool,
          "errors": [{"file": str, "line": int, "column": int, "code": str, "message": str}],
          "warnings": [...],
          "duration_s": float,
          "command": str
        }
    """
    cmd = [sys.executable, CLI_PATH]
    if live_coding:
        cmd.append("--live-coding")
    if dry_run:
        cmd.append("--dry-run")
    if target != "Editor":
        cmd.extend(["--target", target])

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=1800,
            cwd=os.path.dirname(__file__),
        )
        # The CLI already emits JSON on stdout.
        return proc.stdout.strip() or proc.stderr.strip()
    except subprocess.TimeoutExpired:
        return json.dumps({
            "success": False,
            "errors": [{"file": None, "line": None, "column": None,
                        "code": "TIMEOUT", "message": "Build timed out after 1800s"}],
            "warnings": [],
            "duration_s": 0.0,
            "command": " ".join(cmd),
        })


@mcp.tool()
def compile_feedback_health() -> str:
    """Health check for the compile-feedback tool.

    Returns:
        JSON string with the CLI path and whether it exists.
    """
    return json.dumps({
        "cli_path": CLI_PATH,
        "cli_exists": os.path.isfile(CLI_PATH),
        "project_root": os.environ.get("MELODIA_PROJECT_ROOT", "not set"),
    })


def main():
    parser = argparse.ArgumentParser(description="MCP compile-feedback server.")
    parser.add_argument("--transport", choices=["stdio", "sse"], default="stdio",
                        help="Transport (default: stdio).")
    args = parser.parse_args()

    if args.transport == "sse":
        mcp.run(transport="sse")
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
