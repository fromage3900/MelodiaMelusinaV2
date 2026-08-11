"""MCP action browser — discover, schema, test-call tools."""
from __future__ import annotations

from gmm.core import MonolithClient, GmmAudit


def discover_actions(namespace: str | None = None) -> dict:
    """List MCP actions in a namespace (or all)."""
    audit = GmmAudit(action="mkc.discover")
    mc = MonolithClient()
    try:
        result = mc.discover(namespace)
        audit.ok(namespace=namespace or "all", actions=result)
        audit.save("gmm_mcp_discover.json")
        return audit.to_dict()
    except Exception as e:
        audit.fail_from_exception(e)
        audit.save("gmm_mcp_discover.json")
        return audit.to_dict()


def action_schema(namespace: str, action: str) -> dict:
    """Get full param schema for a single MCP action."""
    audit = GmmAudit(action="mkc.action_schema")
    mc = MonolithClient()
    try:
        result = mc.describe_action(namespace, action)
        audit.ok(namespace=namespace, action=action, schema=result)
        audit.save("gmm_mcp_schema.json")
        return audit.to_dict()
    except Exception as e:
        audit.fail_from_exception(e)
        audit.save("gmm_mcp_schema.json")
        return audit.to_dict()


def mcp_status() -> dict:
    """Query Monolith server health."""
    audit = GmmAudit(action="mkc.mcp_status")
    mc = MonolithClient()
    try:
        result = mc.status()
        audit.ok(**result)
        audit.save("gmm_mcp_status.json")
        return audit.to_dict()
    except Exception as e:
        audit.fail_from_exception(e)
        audit.save("gmm_mcp_status.json")
        return audit.to_dict()
