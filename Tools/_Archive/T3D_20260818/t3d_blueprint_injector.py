#!/usr/bin/env python3
"""
T3D Blueprint Injector — injects a complete Blueprint graph spec in a SINGLE
Monolith transaction via `blueprint_query:build_blueprint_from_spec`.

How it works:
1. The caller builds a graph spec (nodes + connections + pin_defaults) with the
   T3DBlueprintInjector helper methods.
2. `inject_into()` submits the whole spec as one JSON-RPC `tools/call` to Monolith.
3. Monolith builds and auto-compiles the Blueprint graph. No template Blueprint,
   no `copy_nodes`, no temp asset, no export_graph round-trip involved.

This is ~10x faster than adding nodes one at a time. Library only — no CLI.
"""

import json, subprocess, sys, os, uuid, tempfile
from pathlib import Path

MONOLITH_URL = "http://127.0.0.1:9316/mcp"

def monolith(action, args=None):
    """Call Monolith MCP tool."""
    body = {
        "jsonrpc": "2.0",
        "id": 1,
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

class T3DBlueprintInjector:
    """
    Batch-injects Blueprint subgraphs using Monolith's build_blueprint_from_spec.
    
    Generates a complete graph spec as JSON and injects all nodes + connections
    in a SINGLE Monolith transaction — ~10x faster than adding nodes one-by-one.
    
    Usage:
        injector = T3DBlueprintInjector()
        injector.add_function_node("id_get", "K2Node_CallFunction", {
            "function": "Get", "target_class": "/Script/BS_GodFile.MelodiaRhythmCombatSubsystem"
        }, [0, 0])
        injector.add_connection("id_get", "then", "id_session", "execute")
        injector.inject_into("/Game/.../BP_BattleController", "EventGraph")
    """
    
    def __init__(self):
        self.node_defs = []
        self.connection_defs = []
        self.pin_defaults = []
        
    def add_function_node(self, node_id, function_name, class_path, position, pin_defaults=None):
        """Add a function call node."""
        self.node_defs.append({
            "id": node_id,
            "type": "function_call",
            "function_name": function_name,
            "target_class": class_path,
            "position": position
        })
        if pin_defaults:
            for pin_name, value in pin_defaults.items():
                self.pin_defaults.append({
                    "node_id": node_id,
                    "pin_name": pin_name,
                    "value": value
                })
    
    def add_get_node(self, node_id, static_function, owner_class, position):
        """Add a static Get function node (for subsystems)."""
        self.node_defs.append({
            "id": node_id,
            "type": "function_call",
            "function_name": static_function,
            "target_class": owner_class,
            "position": position
        })
    
    def add_connection(self, from_node, from_pin, to_node, to_pin):
        """Add a connection between two nodes."""
        self.connection_defs.append({
            "source": from_node,
            "source_pin": from_pin,
            "target": to_node,
            "target_pin": to_pin
        })
    
    def inject_into(self, bp_path, graph_name="EventGraph"):
        """Inject all nodes + connections into a Blueprint graph in ONE transaction."""
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
            print(f"  Result: {json.dumps(parsed, indent=2)[:500]}")
            return parsed
        except:
            print(f"  Inject result: {result[:500]}")
            return result


if __name__ == "__main__":
    print("T3DBlueprintInjector is a library; use it programmatically:")
    print("    injector = T3DBlueprintInjector()")
    print("    injector.add_function_node(...)")
    print("    injector.add_connection(...)")
    print("    injector.inject_into(bp_path, \"EventGraph\")")
