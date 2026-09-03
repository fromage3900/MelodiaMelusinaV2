#!/usr/bin/env python3
"""
T3D Wardrobe Chapter 2 Injector - scaffolds text injection pipeline for
expanded Melodia wardrobe mechanics and ultimate outfit mechanic in Chapter 2.

Extends T3DBlueprintInjector with wardrome-specific node types and
outfit mechanic graph patterns (item grants, stat deltas, flag toggles).

Pipeline integration:
  - Author: wardrobe_ch2_pipeline.json (specs/ folder)
  - Validate: echo_run.py:validate_spec
  - Inject: this injector via Monolith build_blueprint_from_spec
  - Compile: blueprint_query:compile_blueprint (auto via auto_compile:true)
  - Static gates: graph_reachability, bp_live_path, ui_lint, bp_sweep
  - Runtime: pie_smoke_runner, regression_suite
  - Record: record_gate.py <gate-id> pass|fail --note "..."
  - Promote: commit + baseline update + AGENTS.md next-work tick
"""
from __future__ import annotations

import json, uuid, tempfile
from pathlib import Path

MONOLITH_URL = "http://127.0.0.1:9316/mcp"


def monolith(action, args=None):
    """Call Monolith MCP tool."""
    body = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4())[:8],
        "method": "tools/call",
        "params": {"name": action, "arguments": args or {}}
    }
    import urllib.request
    req = urllib.request.Request(
        MONOLITH_URL,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"}
    )
    resp = urllib.request.urlopen(req, timeout=30)
    data = json.loads(resp.read().decode())
    return data.get("result", {}).get("content", [{}])[0].get("text", "")


class T3DWardrobeCh2Injector(T3DBlueprintInjector):
    """
    Wardrobe Chapter 2 extension of T3DBlueprintInjector.

    Adds wardrome-specific patterns:
    - melodia:item:give:<ItemId>:<Count> nodes (logging stub pattern)
    - melodia:stat:<IntentId>:<StatId>:<Delta> nodes (idempotent per IntentId)
    - Flag toggle nodes for outfit state tracking
    - Ultimate outfit mechanic completion checks
    """

    def __init__(self):
        super().__init__()
        self.outfit_mechanic_id = str(uuid.uuid4())

    def add_item_give_node(self, node_id, item_id, count, position):
        """Add a melodia:item:give node (logging stub pattern)."""
        self.add_function_node(node_id, "melodia:item:give", "/Script/BS_GodFile.MelodiaNarrativeSubsystem", position, {
            "item_id": item_id,
            "count": count
        })

    def add_stat_delta_node(self, node_id, intent_id, stat_id, delta, position):
        """Add a melodia:stat delta node (idempotent per IntentId)."""
        self.add_function_node(node_id, "melodia:stat", "/Script/BS_GodFile.MelodiaNarrativeSubsystem", position, {
            "intent_id": intent_id,
            "stat_id": stat_id,
            "delta": delta
        })

    def add_flag_toggle_node(self, node_id, flag_id, state, position):
        """Add a flag toggle node for outfit state tracking."""
        self.add_function_node(node_id, "melodia:flag", "/Script/BS_GodFile.MelodiaNarrativeSubsystem", position, {
            "flag_id": flag_id,
            "state": state
        })

    def add_outfit_mechanic_node(self, node_id, mechanic_key, position):
        """Add an ultimate outfit mechanic chapter 2 node."""
        self.add_function_node(node_id, "melodia:item:give", "/Script/BS_GodFile.MelodiaNarrativeSubsystem", position, {
            "mechanic_key": mechanic_key,
            "chapter": "2",
            "outfit_id": f"outfit_ch2_{self.outfit_mechanic_id}"
        })

    def inject_into(self, bp_path, graph_name="EventGraph"):
        """Inject wardrobe chapter 2 blueprint spec into a Blueprint graph in ONE transaction."""
        result = monolith("blueprint_query", {
            "action": "build_blueprint_from_spec",
            "asset_path": bp_path,
            "graph_name": graph_name,
            "nodes": self.node_defs,
            "connections": self.connection_defs,
            "pin_defaults": self.pin_defaults,
            "auto_compile": True
        })

        try:
            parsed = json.loads(result)
            print(f"  Injected {len(self.node_defs)} nodes + {len(self.connection_defs)} connections")
            print(f"  Result: {json.dumps(parsed, indent=2)[:600]}")
            return parsed
        except Exception as e:
            print(f"  Inject error: {e}")
            print(f"  Raw result: {result[:600]}")
            return result


if __name__ == "__main__":
    print("T3DWardrobeCh2Injector is a library; use it programmatically:")
    print("    injector = T3DWardrobeCh2Injector()")
    print("    injector.add_item_give_node(...)")
    print("    injector.add_stat_delta_node(...)")
    print("    injector.add_flag_toggle_node(...)")
    print("    injector.add_outfit_mechanic_node(...)")
    print("    injector.inject_into(bp_path, \"EventGraph\")")