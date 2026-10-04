#!/usr/bin/env python3
"""Melodia Continuity MCP - portable goal/checkpoint/evidence handoffs.

This server owns only ignored runtime state under Saved/AgentState. It does not
mutate Unreal, DCC assets, Git refs, Perforce, or canonical gameplay data.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Tools.continuity import ContinuityStore, compile_handoff  # noqa: E402
from Tools.mcp_policy import authorize_tool  # noqa: E402


_STORE: ContinuityStore | None = None


def _store() -> ContinuityStore:
    global _STORE
    if _STORE is None:
        _STORE = ContinuityStore(PROJECT_ROOT)
    return _STORE


TOOLS = [
    {
        "name": "continuity_goal_get",
        "description": "Read one durable Melodia agent goal and recent receipts.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "goal_id": {"type": "string"},
                "recent_events": {"type": "integer", "default": 12},
            },
            "required": ["goal_id"],
        },
    },
    {
        "name": "continuity_goal_list",
        "description": "List durable Melodia agent goals, optionally filtered by status.",
        "inputSchema": {
            "type": "object",
            "properties": {"status": {"type": "string"}},
            "required": [],
        },
    },
    {
        "name": "continuity_goal_upsert",
        "description": "Create or update a continuity goal in ignored runtime state.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "goal_id": {"type": "string"},
                "objective": {"type": "string"},
                "phase": {"type": "string", "default": "planning"},
                "status": {"type": "string", "default": "active"},
                "next_action": {"type": ["string", "null"]},
                "metadata": {"type": "object"},
                "actor": {"type": "string", "default": "orchestrator"},
                "approval": {"type": "string", "enum": ["none", "editor", "owner"], "default": "none"},
            },
            "required": ["goal_id", "objective"],
        },
    },
    {
        "name": "continuity_checkpoint",
        "description": "Record a bounded worker checkpoint and optional next action.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "goal_id": {"type": "string"},
                "actor": {"type": "string"},
                "summary": {"type": "string"},
                "completed": {"type": "array", "items": {"type": "string"}},
                "blockers": {"type": "array", "items": {"type": "string"}},
                "next_action": {"type": ["string", "null"]},
                "session": {"type": "object"},
                "approval": {"type": "string", "enum": ["none", "editor", "owner"], "default": "none"},
            },
            "required": ["goal_id", "actor", "summary"],
        },
    },
    {
        "name": "continuity_evidence_add",
        "description": "Attach a commit, test, screenshot, PIE, or other evidence receipt.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "goal_id": {"type": "string"},
                "actor": {"type": "string"},
                "evidence_type": {"type": "string"},
                "uri": {"type": "string"},
                "summary": {"type": "string"},
                "metadata": {"type": "object"},
                "approval": {"type": "string", "enum": ["none", "editor", "owner"], "default": "none"},
            },
            "required": ["goal_id", "actor", "evidence_type", "uri"],
        },
    },
    {
        "name": "continuity_decision_record",
        "description": "Record an explicit architectural or production decision.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "goal_id": {"type": "string"},
                "actor": {"type": "string"},
                "decision": {"type": "string"},
                "rationale": {"type": "string"},
                "supersedes": {"type": ["string", "null"]},
                "approval": {"type": "string", "enum": ["none", "editor", "owner"], "default": "none"},
            },
            "required": ["goal_id", "actor", "decision"],
        },
    },
    {
        "name": "continuity_session_attach",
        "description": "Associate a provider session/thread ID with a durable goal.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "goal_id": {"type": "string"},
                "actor": {"type": "string"},
                "provider": {"type": "string"},
                "session_id": {"type": "string"},
                "model": {"type": ["string", "null"]},
                "workspace": {"type": ["string", "null"]},
                "approval": {"type": "string", "enum": ["none", "editor", "owner"], "default": "none"},
            },
            "required": ["goal_id", "actor", "provider", "session_id"],
        },
    },
    {
        "name": "continuity_handoff_get",
        "description": "Compile a bounded portable context packet for another worker.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "goal_id": {"type": "string"},
                "target": {"type": "string", "default": "generic"},
                "token_budget": {"type": "integer", "default": 4000},
            },
            "required": ["goal_id"],
        },
    },
    {
        "name": "continuity_next_action_set",
        "description": "Set the single highest-priority unfinished action for a goal.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "goal_id": {"type": "string"},
                "next_action": {"type": ["string", "null"]},
                "actor": {"type": "string", "default": "orchestrator"},
                "approval": {"type": "string", "enum": ["none", "editor", "owner"], "default": "none"},
            },
            "required": ["goal_id"],
        },
    },
]

POLICY_OPS = {
    "continuity_goal_get": "read",
    "continuity_goal_list": "read",
    "continuity_goal_upsert": "mutate",
    "continuity_checkpoint": "mutate",
    "continuity_evidence_add": "mutate",
    "continuity_decision_record": "mutate",
    "continuity_session_attach": "mutate",
    "continuity_handoff_get": "read",
    "continuity_next_action_set": "mutate",
}


def call_tool(tool_name: str, args: dict[str, Any]) -> dict[str, Any] | list[dict[str, Any]]:
    operation = POLICY_OPS.get(tool_name)
    if operation is None:
        return {"status": "error", "message": f"Unknown tool: {tool_name}"}

    approval = args.get("approval", "none")
    policy = authorize_tool(tool_name, operation, approval)
    if not policy["allowed"]:
        return {"status": "denied", **policy}

    store = _store()
    if tool_name == "continuity_goal_get":
        return store.get_goal(args["goal_id"], recent_events=args.get("recent_events", 12))
    if tool_name == "continuity_goal_list":
        return store.list_goals(status=args.get("status"))
    if tool_name == "continuity_goal_upsert":
        return store.upsert_goal(
            args["goal_id"],
            args["objective"],
            phase=args.get("phase", "planning"),
            status=args.get("status", "active"),
            next_action=args.get("next_action"),
            metadata=args.get("metadata"),
            actor=args.get("actor", "orchestrator"),
        )
    if tool_name == "continuity_checkpoint":
        return store.checkpoint(
            args["goal_id"],
            actor=args["actor"],
            summary=args["summary"],
            completed=args.get("completed"),
            blockers=args.get("blockers"),
            next_action=args.get("next_action"),
            session=args.get("session"),
        )
    if tool_name == "continuity_evidence_add":
        return store.add_evidence(
            args["goal_id"],
            actor=args["actor"],
            evidence_type=args["evidence_type"],
            uri=args["uri"],
            summary=args.get("summary", ""),
            metadata=args.get("metadata"),
        )
    if tool_name == "continuity_decision_record":
        return store.record_decision(
            args["goal_id"],
            actor=args["actor"],
            decision=args["decision"],
            rationale=args.get("rationale", ""),
            supersedes=args.get("supersedes"),
        )
    if tool_name == "continuity_session_attach":
        return store.attach_session(
            args["goal_id"],
            actor=args["actor"],
            provider=args["provider"],
            session_id=args["session_id"],
            model=args.get("model"),
            workspace=args.get("workspace"),
        )
    if tool_name == "continuity_handoff_get":
        return compile_handoff(
            store,
            args["goal_id"],
            target=args.get("target", "generic"),
            token_budget=args.get("token_budget", 4000),
        )
    if tool_name == "continuity_next_action_set":
        return store.set_next_action(
            args["goal_id"],
            args.get("next_action"),
            actor=args.get("actor", "orchestrator"),
        )
    return {"status": "error", "message": f"Unhandled tool: {tool_name}"}


def main() -> None:
    """Minimal dependency-free MCP stdio loop matching the existing bridge."""
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
            response = {
                "jsonrpc": "2.0",
                "id": rid,
                "result": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "melodia-continuity-mcp", "version": "0.1.0"},
                },
            }
        elif method == "tools/list":
            response = {"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS}}
        elif method == "tools/call":
            try:
                result = call_tool(params.get("name", ""), params.get("arguments", {}))
            except (KeyError, ValueError, TypeError) as exc:
                result = {"status": "error", "message": str(exc)}
            response = {
                "jsonrpc": "2.0",
                "id": rid,
                "result": {
                    "content": [
                        {"type": "text", "text": json.dumps(result, indent=2, ensure_ascii=False)}
                    ]
                },
            }
        elif method == "notifications/initialized":
            continue
        else:
            response = {
                "jsonrpc": "2.0",
                "id": rid,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }

        sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
