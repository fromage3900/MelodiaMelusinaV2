#!/usr/bin/env python3
"""NeMo Guardrails IORails tool-call validation for the MATH harness.

Reads one tool call + the declared tool schemas from stdin as JSON:
    {"tool": "...", "args": {...}, "schemas": [...]}

Builds an IORails-backed NeMo Guardrails config with the
`tool call validation` rail (allowlist + JSON Schema argument conformance,
fail-closed, zero extra LLM calls) and returns a verdict JSON:

    {"engine":"nemo","layer":"nemo-iorails","allowed":bool,
     "reason":str,"detail":{...}}

The verdict `allowed` is ALWAYS a bool so the harness gate can never be left
in an indeterminate state. Run under a Python <=3.13 interpreter
(.venv-guardrails):
    C:\\...\\.venv-guardrails\\Scripts\\python.exe guardrail_nemo_verify.py
"""
from __future__ import annotations

import json
import sys
from typing import Any


def _nemo_verdict(tool_name: str, args: dict[str, Any], schemas: list[dict[str, Any]]) -> dict[str, Any]:
    """Run NeMo Guardrails' actual IORails `tool call validation` rail.

    Uses the rail's own validator (ToolCallRailAction._validate) on a Toolset
    built from the registered Melodia tool schemas. The rail is local and
    model-free: every call must name an allowed tool and its arguments must
    satisfy that tool's JSON Schema, failing closed on any malformed input.
    Raises on failure; the caller falls back to a documented local equivalent.
    """
    from nemoguardrails.guardrails.actions.tool_call_action import ToolCallRailAction
    from nemoguardrails.guardrails.tool_schema import Tool, Toolset
    from nemoguardrails.types import ToolCall, ToolCallFunction

    tools = []
    for t in schemas:
        fn = t.get("function") or {}
        name = fn.get("name")
        if not name:
            continue
        params = fn.get("parameters") or {}
        tools.append(Tool(
            name=name,
            type="function",
            description=fn.get("description"),
            arguments_schema={
                "type": params.get("type", "object"),
                "properties": params.get("properties") or {},
                "required": params.get("required") or [],
            },
        ))
    toolset = Toolset(tools)
    call = ToolCall(id="call_bench_1", type="function",
                    function=ToolCallFunction(name=tool_name, arguments=dict(args or {})))
    result = ToolCallRailAction()._validate(toolset, [call])
    if result.is_safe:
        return {
            "engine": "nemo",
            "layer": "nemo-iorails.tool_call_validation",
            "allowed": True,
            "reason": "tool call and arguments conform to the declared schema",
            "detail": {"rail": "ok", "tool": tool_name},
        }
    return {
        "engine": "nemo",
        "layer": "nemo-iorails.tool_call_validation",
        "allowed": False,
        "reason": result.reason,
        "detail": {"rail": "tool_call_validation"},
    }


def _local_verdict(tool_name: str, args: dict[str, Any], schemas: list[dict[str, Any]]) -> dict[str, Any]:
    """Documented equivalent of the IORails rail (allowlist + schema), fail-closed."""
    allowed_names = {
        (t.get("function") or {}).get("name")
        for t in schemas
        if t.get("type") == "function" and (t.get("function") or {}).get("name")
    }
    by_name = {
        (t.get("function") or {}).get("name"): t.get("function") or {}
        for t in schemas
        if t.get("type") == "function" and (t.get("function") or {}).get("name")
    }

    if tool_name not in allowed_names:
        return {
            "engine": "nemo",
            "layer": "nemo-iorails.tool_call_validation",
            "allowed": False,
            "reason": f"tool call '{tool_name}' is not an allowed tool",
            "detail": {"rail": "allowlist", "tool": tool_name},
        }

    fn = by_name.get(tool_name, {})
    params = fn.get("parameters") or {}
    required = set(params.get("required") or [])
    missing = [r for r in required if r not in (args or {})]
    if missing:
        return {
            "engine": "nemo",
            "layer": "nemo-iorails.tool_call_validation",
            "allowed": False,
            "reason": f"arguments for tool '{tool_name}' do not match its schema: missing required {missing}",
            "detail": {"rail": "argument-schema", "missing": missing},
        }

    props = params.get("properties") or {}
    for key, val in (args or {}).items():
        prop = props.get(key)
        if not prop:
            continue
        prop_type = prop.get("type")
        if prop_type == "string" and not isinstance(val, str):
            return {
                "engine": "nemo",
                "layer": "nemo-iorails.tool_call_validation",
                "allowed": False,
                "reason": f"argument '{key}' must be a string",
                "detail": {"rail": "argument-schema", "arg": key},
            }
        if prop_type == "integer" and not isinstance(val, int):
            return {
                "engine": "nemo",
                "layer": "nemo-iorails.tool_call_validation",
                "allowed": False,
                "reason": f"argument '{key}' must be an integer",
                "detail": {"rail": "argument-schema", "arg": key},
            }
        if prop_type == "number" and not isinstance(val, (int, float)):
            return {
                "engine": "nemo",
                "layer": "nemo-iorails.tool_call_validation",
                "allowed": False,
                "reason": f"argument '{key}' must be a number",
                "detail": {"rail": "argument-schema", "arg": key},
            }
        if prop_type == "boolean" and not isinstance(val, bool):
            return {
                "engine": "nemo",
                "layer": "nemo-iorails.tool_call_validation",
                "allowed": False,
                "reason": f"argument '{key}' must be a boolean",
                "detail": {"rail": "argument-schema", "arg": key},
            }
        enum = prop.get("enum")
        if enum is not None and val not in enum:
            return {
                "engine": "nemo",
                "layer": "nemo-iorails.tool_call_validation",
                "allowed": False,
                "reason": f"argument '{key}' value {val!r} not in allowed enum {enum}",
                "detail": {"rail": "argument-schema", "arg": key, "enum": enum},
            }

    if not props and not required and (args or {}):
        return {
            "engine": "nemo",
            "layer": "nemo-iorails.tool_call_validation",
            "allowed": False,
            "reason": f"tool '{tool_name}' declares no parameters but received arguments",
            "detail": {"rail": "no-argument-tool"},
        }

    return {
        "engine": "nemo",
        "layer": "nemo-iorails.tool_call_validation",
        "allowed": True,
        "reason": "tool call and arguments conform to the declared schema",
        "detail": {"rail": "ok", "tool": tool_name},
    }


def main() -> int:
    payload = json.loads(sys.stdin.read() or "{}")
    tool_name = payload.get("tool", "")
    args = payload.get("args") or {}
    schemas = payload.get("schemas") or []

    try:
        verdict = _nemo_verdict(tool_name, args, schemas)
    except Exception as exc:  # noqa: BLE001
        verdict = _local_verdict(tool_name, args, schemas)
        verdict["detail"] = {
            **verdict.get("detail", {}),
            "mode": "local-rail",
            "iorails_error": str(exc)[:300],
        }
    verdict["allowed"] = bool(verdict["allowed"])
    print(json.dumps(verdict))
    return 0


if __name__ == "__main__":
    sys.exit(main())