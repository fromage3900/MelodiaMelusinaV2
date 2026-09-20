# -*- coding: utf-8 -*-
"""Clear MorningDell body from PCG_MelusinaRoomShell_PCGex and stub RECIPE nodes via PCGex Settings classes.
Wiring/pins may still need editor pass — receipt lists what landed.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

EAL = unreal.EditorAssetLibrary
SAVED = Path(unreal.Paths.project_saved_dir()) / "Audit"
OUT = SAVED / "pcgex_roomshell_clear_author_2026-09-20.json"
GRAPH = "/Game/EnvSandbox/PCG/House/PCG_MelusinaRoomShell_PCGex"

# Prefer PCGex Settings class names discovered in project
RECIPE_NODES = [
    ("seed_create_points", "PCGCreatePointsSettings", "CreatePoints"),
    ("shape_polygon", "PCGExCreateShapePolygonSettings", "PCGEx Shape Polygon"),
    ("create_shapes", "PCGExCreateShapesSettings", "PCGEx Create Shapes"),
    ("shape_grid", "PCGExCreateShapeGridSettings", "PCGEx Shape Grid"),
    ("subdivide_path", "PCGExSubdivideSettings", "PCGEx Subdivide"),
    ("offset_path", "PCGExOffsetPathSettings", "PCGEx Offset Path"),
    ("path_filter", "PCGExPathFilterSettings", "PCGEx Path Filter"),
    ("floor_spawner", "PCGStaticMeshSpawnerSettings", "Static Mesh Spawner"),
    ("wall_spawner", "PCGStaticMeshSpawnerSettings", "Static Mesh Spawner"),
    ("create_spline", "PCGExCreateSplineSettings", "PCGEx Create Spline"),
]


def _cls(name):
    try:
        return getattr(unreal, name)
    except Exception:
        return None


def _list_nodes(graph):
    out = []
    for attr in ("nodes", "get_nodes", "get_all_nodes"):
        try:
            v = getattr(graph, attr)
            v = v() if callable(v) else v
            if v:
                return list(v)
        except Exception:
            pass
    try:
        return list(graph.get_editor_property("nodes") or [])
    except Exception:
        return []


def _clear_nodes(graph):
    removed = []
    nodes = _list_nodes(graph)
    for n in list(nodes):
        name = None
        try:
            name = n.get_name()
        except Exception:
            name = str(n)
        ok = False
        for meth in ("remove_node", "RemoveNode"):
            try:
                fn = getattr(graph, meth)
                fn(n)
                ok = True
                break
            except Exception:
                pass
        if not ok:
            try:
                unreal.PCGGraph.remove_node(graph, n)
                ok = True
            except Exception:
                pass
        removed.append({"name": name, "removed": ok})
    return removed


def _add_node(graph, settings_cls, label):
    # Try common UE PCG add_node signatures
    errs = []
    for call in (
        lambda: graph.add_node(settings_cls),
        lambda: graph.add_node(settings_cls()),
        lambda: unreal.PCGGraph.add_node(graph, settings_cls),
        lambda: graph.add_node_of_class(settings_cls),
    ):
        try:
            node = call()
            if node:
                try:
                    node.set_editor_property("node_title", label)
                except Exception:
                    pass
                return node, None
        except Exception as e:
            errs.append(str(e))
    # Settings object then add_node_instance
    try:
        settings = unreal.new_object(settings_cls)
        for call in (
            lambda: graph.add_node_instance(settings),
            lambda: graph.add_node(settings),
        ):
            try:
                node = call()
                if node:
                    return node, None
            except Exception as e:
                errs.append(str(e))
    except Exception as e:
        errs.append("new_object:" + str(e))
    return None, errs[:6]


def main():
    report = {
        "schema": "melodia.pcgex_roomshell_clear_author.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "graph": GRAPH,
        "cleared": [],
        "added": [],
        "ok": False,
        "notes": [],
    }
    if not EAL.does_asset_exist(GRAPH):
        report["error"] = "graph_missing"
        OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("AUTHOR_ERR missing")
        return 1

    graph = EAL.load_asset(GRAPH)
    before = [getattr(n, "get_name", lambda: str(n))() for n in _list_nodes(graph)]
    report["before_count"] = len(before)
    report["before_sample"] = before[:12]

    report["cleared"] = _clear_nodes(graph)
    after_clear = _list_nodes(graph)
    report["after_clear_count"] = len(after_clear)
    if after_clear:
        report["notes"].append("clear_incomplete_manual_delete_may_be_needed")

    for key, cls_name, label in RECIPE_NODES:
        cls = _cls(cls_name)
        entry = {"key": key, "class": cls_name, "label": label}
        if not cls:
            entry["ok"] = False
            entry["error"] = "class_not_in_unreal_module"
            report["added"].append(entry)
            continue
        node, errs = _add_node(graph, cls, label)
        entry["ok"] = node is not None
        if node:
            try:
                entry["name"] = node.get_name()
            except Exception:
                entry["name"] = str(node)
        else:
            entry["errors"] = errs
        report["added"].append(entry)

    report["after_count"] = len(_list_nodes(graph))
    try:
        EAL.save_asset(GRAPH)
        report["saved"] = True
    except Exception as e:
        report["saved"] = str(e)

    added_ok = sum(1 for a in report["added"] if a.get("ok"))
    report["ok"] = report["after_clear_count"] == 0 or added_ok > 0
    report["notes"].append(
        "Pins/wiring + Width/Depth/Height params still editor/RECIPE pass; "
        "this script only clears MorningDell and stubs Settings nodes."
    )
    OUT.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(
        "AUTHOR "
        + json.dumps(
            {
                "before": report["before_count"],
                "after_clear": report["after_clear_count"],
                "added_ok": added_ok,
                "after": report["after_count"],
                "saved": report.get("saved"),
            }
        )
    )
    unreal.log("AUTHOR wrote " + str(OUT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
