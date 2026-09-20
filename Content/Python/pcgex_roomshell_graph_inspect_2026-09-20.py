# -*- coding: utf-8 -*-
"""Read-only: list nodes/params on PCG_MelusinaRoomShell_PCGex (MorningDell donor) and compare to RECIPE."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

EAL = unreal.EditorAssetLibrary
SAVED = Path(unreal.Paths.project_saved_dir()) / "Audit"
OUT = SAVED / "pcgex_roomshell_graph_inspect_2026-09-20.json"
GRAPH = "/Game/EnvSandbox/PCG/House/PCG_MelusinaRoomShell_PCGex"
BP = "/Game/EnvSandbox/Blueprints/House/BP_MelusinaRoomShell"

def main():
    report = {
        "schema": "melodia.pcgex_roomshell_graph_inspect.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "graph": GRAPH,
        "nodes": [],
        "params": [],
        "bp_components": [],
        "recipe_gaps": [],
    }
    if not EAL.does_asset_exist(GRAPH):
        report["error"] = "graph_missing"
        OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("INSPECT_ERR")
        return 1
    g = EAL.load_asset(GRAPH)
    # nodes
    try:
        nodes = list(g.get_editor_property("nodes") or [])
    except Exception:
        try:
            nodes = list(getattr(g, "nodes", []) or [])
        except Exception:
            nodes = []
    for n in nodes:
        entry = {"class": str(type(n).__name__), "str": str(n)[:200]}
        try:
            entry["title"] = str(n.get_editor_property("node_title") or "")
        except Exception:
            pass
        try:
            entry["name"] = n.get_name()
        except Exception:
            pass
        for attr in ("settings", "node_title", "bEnabled"):
            try:
                entry[attr] = str(n.get_editor_property(attr))[:120]
            except Exception:
                pass
        report["nodes"].append(entry)
    # graph parameters / user params
    for prop in ("user_parameters", "graph_parameters", "params", "exposed_parameters"):
        try:
            v = g.get_editor_property(prop)
            report["params"].append({prop: str(v)[:500]})
        except Exception:
            pass
    # BP SCS components
    if EAL.does_asset_exist(BP):
        bp = EAL.load_asset(BP)
        try:
            scs = bp.simple_construction_script
            for n in list(scs.get_all_nodes() or []):
                try:
                    report["bp_components"].append({
                        "name": n.get_name(),
                        "class": str(n.component_class),
                    })
                except Exception as e:
                    report["bp_components"].append({"err": str(e)})
        except Exception as e:
            report["bp_scs_err"] = str(e)
    # recipe checklist
    blob = json.dumps(report["nodes"]).lower()
    needed = [
        ("rectangle_or_shape", ["rect", "shape", "create path", "createpoints", "spline"]),
        ("floor_grid", ["grid", "surface", "floor", "sampler", "density"]),
        ("wall_perimeter", ["wall", "path", "boundary", "edge", "difference"]),
        ("door_filter", ["door", "filter", "cut", "boolean"]),
        ("mesh_spawner", ["static mesh", "spawner", "mesh"]),
        ("pcgex", ["pcgex", "ex path", "ex filter"]),
    ]
    for label, keys in needed:
        hit = any(k in blob for k in keys)
        report["recipe_gaps"].append({"need": label, "present_hint": hit})
    report["node_count"] = len(report["nodes"])
    OUT.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print("INSPECT " + json.dumps({"nodes": len(report["nodes"]), "gaps": report["recipe_gaps"]}))
    unreal.log("INSPECT wrote " + str(OUT))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
