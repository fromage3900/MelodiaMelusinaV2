"""Monolith Kit Combo — MCP action browser, pipeline tools, BP ops, asset tools.

Phase 5 deliverable — currently scaffolding stubs.
"""
from __future__ import annotations

from gmm.mkc.actions import discover_actions, action_schema, mcp_status
from gmm.mkc.pipeline import verify_all, verify_via_mcp

__all__ = [
    "discover_actions",
    "action_schema",
    "mcp_status",
    "verify_all",
    "verify_via_mcp",
]