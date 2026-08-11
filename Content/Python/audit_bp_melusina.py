"""Audit BP_Melusina graph nodes for compile blockers.

Run from UE:
    py Content/Python/audit_bp_melusina.py
"""
from __future__ import annotations

import json
import os
import unreal


BP_PATH = "/Game/Melodia/Characters/Melusina/BP_Melusina"
REPORT_PATH = "G:/EnvironmentPortfolio/BS_GodFile/Saved/Melodia/BP_Melusina_audit.json"


def _pin_summary(pin):
    return {
        "name": str(pin.pin_name),
        "direction": str(pin.direction),
        "default": str(pin.default_value),
        "linked_to": [str(linked.get_outer().get_name()) for linked in pin.linked_to],
    }


def audit():
    bp = unreal.EditorAssetLibrary.load_asset(BP_PATH)
    if not bp:
        raise RuntimeError(f"Could not load {BP_PATH}")

    generated_class = None
    try:
        generated_class = bp.get_editor_property("generated_class")
    except Exception:
        generated_class = None

    result = {
        "asset": BP_PATH,
        "generated_class": str(generated_class.get_path_name()) if generated_class else "",
        "graphs": [],
        "spawn_nodes": [],
    }

    graphs = []
    try:
        graphs = list(unreal.BlueprintEditorLibrary.list_graphs(bp) or [])
    except Exception as exc:
        result.setdefault("warnings", []).append(f"list_graphs: {exc}")

    for graph in graphs:
        try:
            nodes = list(graph.get_editor_property("nodes") or [])
        except Exception as exc:
            result.setdefault("warnings", []).append(f"{graph.get_name()}.nodes: {exc}")
            nodes = []

        graph_entry = {
            "name": graph.get_name(),
            "node_count": len(nodes),
        }
        result["graphs"].append(graph_entry)

        for node in nodes:
            node_class = node.get_class().get_name()
            node_title = ""
            try:
                node_title = str(node.get_node_title(unreal.NodeTitleType.FULL_TITLE))
            except Exception:
                node_title = node.get_name()

            if "Spawn" not in node_title and "Spawn" not in node_class:
                continue

            entry = {
                "graph": graph.get_name(),
                "name": node.get_name(),
                "class": node_class,
                "title": node_title,
                "position": [node.node_pos_x, node.node_pos_y],
                "pins": [_pin_summary(pin) for pin in node.pins],
            }
            result["spawn_nodes"].append(entry)

    os.makedirs("G:/EnvironmentPortfolio/BS_GodFile/Saved/Melodia", exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)

    unreal.log(f"[MelodiaAudit] Wrote {REPORT_PATH}")
    unreal.log(f"[MelodiaAudit] Found {len(result['spawn_nodes'])} spawn-like node(s)")


if __name__ == "__main__":
    audit()
