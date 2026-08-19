#!/usr/bin/env python3
"""Small, dependency-free authorization layer for agent/MCP tool calls."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "specs" / "mcp_tool_policy.v1.json"
_RANKS = {"none": 0, "editor": 1, "owner": 2}


def load_policy() -> dict[str, Any]:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def approval_satisfies(granted: str, required: str) -> bool:
    return _RANKS.get(granted, -1) >= _RANKS.get(required, 99)


def _normalise_path(value: str | None) -> str:
    return str(value or "").replace("\\", "/").lower()


def authorize_tool(
    tool_name: str,
    operation: str,
    approval: str = "none",
    path: str | None = None,
) -> dict[str, Any]:
    """Return a structured decision; never execute the tool itself."""
    policy = load_policy()
    normalised = _normalise_path(path)
    for token in policy.get("forbidden_path_tokens", []):
        if str(token).lower() in normalised:
            return {
                "allowed": False,
                "tool": tool_name,
                "operation": operation,
                "reason": f"forbidden path policy matched: {token}",
            }

    entry = policy.get("tools", {}).get(tool_name)
    if not entry:
        return {
            "allowed": False,
            "tool": tool_name,
            "operation": operation,
            "reason": "tool is not explicitly declared in the policy",
        }
    if entry.get("decision") != "allow":
        return {
            "allowed": False,
            "tool": tool_name,
            "operation": operation,
            "reason": entry.get("reason", "tool is denied by policy"),
        }
    if operation not in entry.get("operations", []):
        return {
            "allowed": False,
            "tool": tool_name,
            "operation": operation,
            "reason": "operation is not declared for this tool",
        }
    required = entry.get("required_approval", "none")
    if not approval_satisfies(approval, required):
        return {
            "allowed": False,
            "tool": tool_name,
            "operation": operation,
            "required_approval": required,
            "granted_approval": approval,
            "reason": f"requires {required} approval",
        }
    return {
        "allowed": True,
        "tool": tool_name,
        "operation": operation,
        "required_approval": required,
        "granted_approval": approval,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Authorize one Melodia MCP tool operation")
    parser.add_argument("tool")
    parser.add_argument("operation")
    parser.add_argument("--approval", default="none", choices=sorted(_RANKS))
    parser.add_argument("--path")
    args = parser.parse_args()
    print(json.dumps(authorize_tool(args.tool, args.operation, args.approval, args.path), indent=2))
