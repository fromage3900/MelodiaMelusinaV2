#!/usr/bin/env python3
"""Validate the checked-in MCP registration against the Melodia tool policy."""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _first_existing(*paths: Path) -> Path:
    for path in paths:
        if path.is_file():
            return path
    return paths[0]


def validate() -> dict:
    session_config = load_json(_first_existing(ROOT / ".mcp.json", ROOT.parent / ".mcp.json"))
    jcode_config = load_json(_first_existing(ROOT / ".jcode" / "mcp.json", ROOT.parent / ".jcode" / "mcp.json"))
    policy = load_json(ROOT / "specs" / "mcp_tool_policy.v1.json")
    bridge = importlib.import_module("deploy.agent_bridge_mcp")

    session_servers = session_config.get("mcpServers", {})
    jcode_servers = jcode_config.get("mcpServers", {})
    exposed_tools = {entry["name"] for entry in bridge.TOOLS}
    policy_tools = set(policy.get("tools", {}))

    checks = {
        "agent_bridge_registered_in_session": "agent_bridge" in session_servers,
        "agent_bridge_registered_in_jcode": "agent_bridge" in jcode_servers,
        "agent_bridge_entrypoint_exists": (ROOT / "deploy" / "agent_bridge_mcp.py").is_file(),
        "every_bridge_tool_has_policy_entry": exposed_tools <= policy_tools,
        "raw_ue_editor_command_denied": policy.get("tools", {}).get("ue_editor_command", {}).get("decision") == "deny",
        "policy_default_is_deny": policy.get("default_decision") == "deny",
    }
    return {
        "schema": "melodia.mcp_registration_check.v1",
        "status": "pass" if all(checks.values()) else "fail",
        "servers": {
            "session": sorted(session_servers),
            "jcode": sorted(jcode_servers),
        },
        "bridge_tools": sorted(exposed_tools),
        "missing_policy_entries": sorted(exposed_tools - policy_tools),
        "checks": checks,
    }


def main() -> int:
    result = validate()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
