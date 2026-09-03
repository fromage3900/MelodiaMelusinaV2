#!/usr/bin/env python3
"""Pluggable guardrail layer for the MATH (Melodia Agent Test Harness) eval loop.

Intercepts a model's chosen tool call BEFORE execution and returns an
allow/deny verdict. Two layers, both local and cheap:

  policy  (default, always available)
    Reuses the production default-deny authorization gate
    (Tools/mcp_policy.py / specs/mcp_tool_policy.v1.json). Denies unknown
    tools, disallowed operations, and forbidden path tokens. This is the
    exact gate production melodia_mcp_server.py applies on every tools/call.

  nemo    (optional, needs Python <=3.13)
    Shells out to the .venv-guardrails interpreter and validates the same
    call against NeMo Guardrails' IORails `tool call validation` rail
    (allowlist + JSON Schema argument conformance, fail-closed). Falls back
    to a documented local equivalent when nemoguardrails cannot be imported.

CLI:
    python guardrail_gate.py <tool_name> <args_json> --mode policy
    python guardrail_gate.py <tool_name> <args_json> --mode nemo
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "Tools"
VENV_PY = ROOT / ".venv-guardrails" / "Scripts" / "python.exe"
NEMO_VERIFIER = TOOLS / "guardrail_nemo_verify.py"


def _tool_schemas() -> list[dict[str, Any]]:
    """Return the registered Melodia tool schemas in OpenAI function-tool shape."""
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(TOOLS))
    try:
        import deploy.melodia_mcp_server as server
        tools = getattr(server, "TOOLS", [])
    except Exception:
        return []
    out = []
    for tool in tools:
        name = tool.get("name")
        desc = tool.get("description", "")
        schema = tool.get("inputSchema") or tool.get("input_schema") or {}
        out.append({
            "type": "function",
            "function": {"name": name, "description": desc, "parameters": schema},
        })
    return out


def _policy_decision(tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Run the production default-deny gate (Tools/mcp_policy.py)."""
    sys.path.insert(0, str(TOOLS))
    from mcp_policy import authorize_tool

    path_hint = None
    for key in ("path", "asset_path", "abp_path", "metasound_path", "widget_path",
                "fixture_name", "template_id", "dungeon_id", "quest_id", "encounter_id"):
        if key in args:
            path_hint = args[key]
            break
    decision = authorize_tool(tool_name, "read", approval="none", path=path_hint)
    return {
        "engine": "policy",
        "layer": "mcp_policy.default-deny",
        "allowed": bool(decision.get("allowed")),
        "reason": decision.get("reason", "allowed by policy"),
        "detail": decision,
    }


def _nemo_decision(tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Validate through NeMo Guardrails IORails tool-call validation (venv)."""
    schemas = _tool_schemas()
    if not VENV_PY.exists():
        return {
            "engine": "nemo",
            "layer": "nemo-iorails",
            "allowed": True,
            "reason": "nemo unavailable (.venv-guardrails missing) - bypassed by harness",
            "detail": {"mode": "bypass", "why": "no venv interpreter"},
        }
    payload = json.dumps({"tool": tool_name, "args": args, "schemas": schemas})
    try:
        proc = subprocess.run(
            [str(VENV_PY), str(NEMO_VERIFIER)],
            input=payload.encode("utf-8"),
            capture_output=True,
            timeout=60,
        )
        out = proc.stdout.decode("utf-8", errors="replace").strip()
        if proc.returncode == 0 and out:
            return json.loads(out)
        return {
            "engine": "nemo",
            "layer": "nemo-iorails",
            "allowed": False,
            "reason": f"nemo verifier failed (rc={proc.returncode}): {out or proc.stderr.decode(errors='replace')[:200]}",
            "detail": {"mode": "error", "rc": proc.returncode},
        }
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "engine": "nemo",
            "layer": "nemo-iorails",
            "allowed": False,
            "reason": f"nemo verifier exception: {exc}",
            "detail": {"mode": "error", "error": str(exc)},
        }


def guard(tool_name: str, args: dict[str, Any], mode: str) -> dict[str, Any]:
    """Return an allow/deny verdict for one tool call."""
    verdict = _policy_decision(tool_name, args)
    if mode == "nemo":
        nemo = _nemo_decision(tool_name, args)
        if nemo.get("detail", {}).get("mode") == "bypass":
            # venv missing - policy gate is the enforcement; record the bypass.
            verdict["nemo"] = nemo
        else:
            verdict = {
                "engine": "nemo",
                "layer": "nemo-iorails + policy",
                "allowed": verdict["allowed"] and nemo["allowed"],
                "reason": "; ".join(
                    r for r in (verdict.get("reason"), nemo.get("reason")) if r
                ),
                "detail": {"policy": verdict, "nemo": nemo},
            }
    return verdict


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tool_name")
    parser.add_argument("args_json", nargs="?", default="{}")
    parser.add_argument("--mode", choices=("policy", "nemo"), default="policy")
    parser.add_argument("--schemas", action="store_true", help="dump registered tool schemas")
    args = parser.parse_args(argv)

    if args.schemas:
        print(json.dumps(_tool_schemas(), indent=2))
        return 0

    try:
        args_obj = json.loads(args.args_json or "{}")
    except json.JSONDecodeError:
        args_obj = {}
    print(json.dumps(guard(args.tool_name, args_obj, args.mode), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())