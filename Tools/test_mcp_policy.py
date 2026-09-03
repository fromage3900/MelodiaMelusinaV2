#!/usr/bin/env python3
"""Pure tests for the MCP/JCODE mutation policy."""
from __future__ import annotations

from mcp_policy import authorize_tool


def test_policy() -> None:
    assert authorize_tool("get_agent_status", "read")["allowed"]
    assert not authorize_tool("run_blessing_evolution", "mutate")["allowed"]
    assert authorize_tool("run_blessing_evolution", "mutate", "owner")["allowed"]
    assert not authorize_tool("ue_editor_command", "mutate", "owner")["allowed"]
    assert authorize_tool("t3d_safe_wire", "mutate", "editor")["allowed"]
    assert not authorize_tool("blueprint_query.inject_nodes_t3d", "mutate")["allowed"]
    assert authorize_tool("blueprint_query.inject_nodes_t3d", "mutate", "editor")["allowed"]
    assert not authorize_tool("t3d_safe_wire", "mutate", "editor", "Content/_PROJECT/foo.uasset")["allowed"]


if __name__ == "__main__":
    test_policy()
    print("mcp-policy-tests: 8/8 passed")
