#!/usr/bin/env python
"""
t3d_demo.py - T3D Pipeline Demo
Wires multiple Blueprints simultaneously via Monolith MCP blueprint_query build_blueprint_from_spec.

Launches 4 injections in parallel:
  1. BP_BattleController     - 3 MELUSINA_LOOP log markers wired to the result matrix
  2. BP_MelodiaBattleUI      - Heartbeat pulse animation on MelodiaNoteHighway when visible
  3. BP_MelodiaJRPGGameInstance - Loop counter counting completed battles
  4. BP_InteractionBattle    - Log node when encounter is triggered

Usage:
    python Tools/t3d_demo.py

Requires:
    - Monolith MCP server running at localhost:9316/mcp
    - httpx (pip install httpx)
"""
from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx

MCP_URL = "http://localhost:9316/mcp"
REQUEST_TIMEOUT = 120


# ---------------------------------------------------------------------------
# Blueprint specs
# ---------------------------------------------------------------------------

SPECS = [
    # --- 1. BP_BattleController: 3 MELUSINA_LOOP markers on result matrix ---
    {
        "asset_path": "/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController",
        "graph_name": "EventGraph",
        "nodes": [
            {
                "id": "print_victory",
                "type": "function_call",
                "function_name": "PrintString",
                "function_class": "/Script/Engine.KismetSystemLibrary",
                "position": {"x": 600, "y": -120},
            },
            {
                "id": "print_defeat",
                "type": "function_call",
                "function_name": "PrintString",
                "function_class": "/Script/Engine.KismetSystemLibrary",
                "position": {"x": 600, "y": 80},
            },
            {
                "id": "print_flee",
                "type": "function_call",
                "function_name": "PrintString",
                "function_class": "/Script/Engine.KismetSystemLibrary",
                "position": {"x": 600, "y": 280},
            },
        ],
        "connections": [
            {"source": "ResultMatrix", "source_pin": "Victory", "target": "print_victory", "target_pin": "execute"},
            {"source": "ResultMatrix", "source_pin": "Defeat", "target": "print_defeat", "target_pin": "execute"},
            {"source": "ResultMatrix", "source_pin": "Flee", "target": "print_flee", "target_pin": "execute"},
        ],
        "pin_defaults": [
            {"node_id": "print_victory", "pin_name": "InString", "value": "MELUSINA_LOOP: Battle Victory"},
            {"node_id": "print_defeat", "pin_name": "InString", "value": "MELUSINA_LOOP: Battle Defeat"},
            {"node_id": "print_flee", "pin_name": "InString", "value": "MELUSINA_LOOP: Battle Flee"},
            {"node_id": "print_victory", "pin_name": "bPrintToScreen", "value": True},
            {"node_id": "print_defeat", "pin_name": "bPrintToScreen", "value": True},
            {"node_id": "print_flee", "pin_name": "bPrintToScreen", "value": True},
        ],
        "auto_compile": True,
    },
    # --- 2. BP_MelodiaBattleUI: Heartbeat pulse on MelodiaNoteHighway ---
    {
        "asset_path": "/Game/MelodiaIntegration/UI/BP_MelodiaBattleUI",
        "graph_name": "EventGraph",
        "nodes": [
            {
                "id": "is_visible_check",
                "type": "function_call",
                "function_name": "IsVisible",
                "function_class": "/Script/Engine.KismetSystemLibrary",
                "position": {"x": 400, "y": 0},
            },
            {
                "id": "branch_visible",
                "type": "function_call",
                "function_name": "Branch",
                "function_class": "/Script/Engine.KismetSystemLibrary",
                "position": {"x": 600, "y": 0},
            },
            {
                "id": "delay_heartbeat",
                "type": "function_call",
                "function_name": "Delay",
                "function_class": "/Script/Engine.KismetSystemLibrary",
                "position": {"x": 800, "y": -60},
            },
            {
                "id": "pulse_highway",
                "type": "function_call",
                "function_name": "PrintString",
                "function_class": "/Script/Engine.KismetSystemLibrary",
                "position": {"x": 1000, "y": -60},
            },
        ],
        "connections": [
            {"source": "MelodiaNoteHighway", "source_pin": "OnVisibilityChanged", "target": "is_visible_check", "target_pin": "execute"},
            {"source": "is_visible_check", "source_pin": "ReturnValue", "target": "branch_visible", "target_pin": "Condition"},
            {"source": "is_visible_check", "source_pin": "execute", "target": "branch_visible", "target_pin": "execute"},
            {"source": "branch_visible", "source_pin": "True", "target": "delay_heartbeat", "target_pin": "execute"},
            {"source": "delay_heartbeat", "source_pin": "Completed", "target": "pulse_highway", "target_pin": "execute"},
        ],
        "pin_defaults": [
            {"node_id": "delay_heartbeat", "pin_name": "Duration", "value": 0.8},
            {"node_id": "pulse_highway", "pin_name": "InString", "value": "MELUSINA_LOOP: Highway Heartbeat Pulse"},
            {"node_id": "pulse_highway", "pin_name": "bPrintToScreen", "value": True},
        ],
        "auto_compile": True,
    },
    # --- 3. BP_MelodiaJRPGGameInstance: Loop counter ---
    {
        "asset_path": "/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameInstance",
        "graph_name": "EventGraph",
        "nodes": [
            {
                "id": "increment_counter",
                "type": "function_call",
                "function_name": "PrintString",
                "function_class": "/Script/Engine.KismetSystemLibrary",
                "position": {"x": 500, "y": 0},
            },
            {
                "id": "grant_shard",
                "type": "function_call",
                "function_name": "TryGrantShards",
                "function_class": "/Script/MelodiaCore.MelodiaTokenWalletSubsystem",
                "position": {"x": 500, "y": 200},
            },
        ],
        "connections": [
            {"source": "OnBattleCompleted", "source_pin": "execute", "target": "increment_counter", "target_pin": "execute"},
            {"source": "increment_counter", "source_pin": "execute", "target": "grant_shard", "target_pin": "execute"},
        ],
        "pin_defaults": [
            {"node_id": "increment_counter", "pin_name": "InString", "value": "MELUSINA_LOOP: Battle loop counter ++"},
            {"node_id": "increment_counter", "pin_name": "bPrintToScreen", "value": True},
            {"node_id": "grant_shard", "pin_name": "ShardCount", "value": 1},
        ],
        "auto_compile": True,
    },
    # --- 4. BP_InteractionBattle: Encounter trigger log ---
    {
        "asset_path": "/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_InteractionBattle",
        "graph_name": "EventGraph",
        "nodes": [
            {
                "id": "log_encounter",
                "type": "function_call",
                "function_name": "PrintString",
                "function_class": "/Script/Engine.KismetSystemLibrary",
                "position": {"x": 400, "y": 0},
            },
        ],
        "connections": [
            {"source": "OnEncounterTriggered", "source_pin": "execute", "target": "log_encounter", "target_pin": "execute"},
        ],
        "pin_defaults": [
            {"node_id": "log_encounter", "pin_name": "InString", "value": "MELUSINA_LOOP: Encounter triggered by player"},
            {"node_id": "log_encounter", "pin_name": "bPrintToScreen", "value": True},
        ],
        "auto_compile": True,
    },
]


# ---------------------------------------------------------------------------
# MCP transport
# ---------------------------------------------------------------------------

def call_build_blueprint(spec: dict) -> dict:
    """Dispatch build_blueprint_from_spec on the Monolith MCP server.

    Blueprint actions are not top-level tools; they are dispatched through the
    `blueprint_query` wrapper with `arguments.action` set to the action name
    and the action's params passed alongside it.
    """
    params = dict(spec)
    params["action"] = "build_blueprint_from_spec"
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "blueprint_query",
            "arguments": params,
        },
    }
    with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
        resp = client.post(MCP_URL, json=payload)
        resp.raise_for_status()
        return resp.json()


def run_spec(spec: dict) -> dict:
    """Run a single blueprint spec and return the result with a label."""
    label = spec["asset_path"].rsplit("/", 1)[-1]
    try:
        result = call_build_blueprint(spec)
        return {"label": label, "ok": True, "result": result}
    except Exception as e:
        return {"label": label, "ok": False, "error": str(e)}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    print("=" * 60)
    print("T3D Pipeline Demo - Simultaneous Blueprint Injection")
    print("=" * 60)
    print(f"Target MCP: {MCP_URL}")
    print(f"Blueprints to wire: {len(SPECS)}")
    print()

    results = []
    with ThreadPoolExecutor(max_workers=len(SPECS)) as pool:
        futures = {pool.submit(run_spec, spec): spec for spec in SPECS}
        for future in as_completed(futures):
            r = future.result()
            results.append(r)
            status = "OK" if r["ok"] else "FAIL"
            print(f"  [{status}] {r['label']}")

    print()
    print("-" * 60)
    print("Summary")
    print("-" * 60)

    ok_count = sum(1 for r in results if r["ok"])
    fail_count = sum(1 for r in results if not r["ok"])
    print(f"  Compiled: {ok_count}/{len(results)}")
    print(f"  Errors:   {fail_count}")

    if fail_count > 0:
        print()
        for r in results:
            if not r["ok"]:
                print(f"  ! {r['label']}: {r['error']}")

    print()
    print("Done.")
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
