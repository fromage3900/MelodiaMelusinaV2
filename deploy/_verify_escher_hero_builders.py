"""Evaluate the four Escher/Dream hero GN builders in Blender 5.2.

Usage:
  blender --background --factory-startup --python deploy/_verify_escher_hero_builders.py

The report is written to Saved/Audit/escher_hero_builders.json. This deliberately
checks evaluated geometry and parameter response instead of only node/link counts.
"""

from __future__ import annotations

import json
import os
import sys

import bpy


DEPLOY = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(DEPLOY)
REPORT_PATH = os.path.join(PROJECT_ROOT, "Saved", "Audit", "escher_hero_builders.json")
if DEPLOY not in sys.path:
    sys.path.insert(0, DEPLOY)


TARGETS = {
    "MEL_escher_penrose_stairs": {
        "label": "Escher Penrose Stairs",
        "params": {"Runs": 4, "Steps per Run": 5, "Second Loop": True},
        "probes": [
            {"name": "steps_response", "params": {"Steps per Run": 8}, "metric": "vertices"},
            {"name": "run_response", "params": {"Runs": 6}, "metric": "vertices"},
            {"name": "second_loop_gate", "params": {"Second Loop": False}, "metric": "vertices"},
        ],
    },
    "MEL_escher_belvedere": {
        "label": "Escher Belvedere",
        "params": {"Upper Rotation": 45.0, "Tall Threading Columns": True},
        "probes": [
            {"name": "column_grid_response", "params": {"Column Count X": 4}, "metric": "vertices"},
            {"name": "rotation_response", "params": {"Upper Rotation": 0.0}, "metric": "bounds"},
        ],
    },
    "MEL_escher_waterfall": {
        "label": "Escher Waterfall",
        "params": {"Channel Length X": 6.0, "Channel Length Y": 4.5, "Cascade": True},
        "probes": [
            {"name": "side_length_response", "params": {"Channel Length Y": 8.0}, "metric": "bounds"},
            {"name": "drop_response", "params": {"Side Drop": 1.0}, "metric": "bounds"},
        ],
    },
    "MEL_sky_observatory": {
        "label": "Celestial Dream Observatory",
        "params": {"Ring Count": 4, "Planets": True, "Lanterns": True, "Deck Railing": True},
        "probes": [
            {"name": "ring_count_response", "params": {"Ring Count": 0}, "metric": "vertices"},
            {"name": "lantern_gate", "params": {"Lanterns": False}, "metric": "vertices"},
            {"name": "deck_gate", "params": {"Deck Railing": False}, "metric": "vertices"},
        ],
    },
}


def _input_sockets(tree):
    interface = getattr(tree, "interface", None)
    if interface is None:
        return {}
    result = {}
    for item in interface.items_tree:
        if getattr(item, "item_type", "") == "SOCKET" and getattr(item, "in_out", "") == "INPUT":
            result[item.name] = item
    return result


def _set_modifier_inputs(modifier, tree, params):
    sockets = _input_sockets(tree)
    missing = []
    for name, value in params.items():
        socket = sockets.get(name)
        if socket is None:
            missing.append(name)
            continue
        # Factory-startup modifiers do not expose ID-property writes until the
        # group is attached to a fully registered object context. Setting the
        # interface default is deterministic for this isolated evaluator and
        # still exercises the same GN input path.
        socket.default_value = value
    return missing


def _evaluate(obj):
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        vertices = len(mesh.vertices)
        faces = len(mesh.polygons)
        if vertices:
            xs = [v.co.x for v in mesh.vertices]
            ys = [v.co.y for v in mesh.vertices]
            zs = [v.co.z for v in mesh.vertices]
            bounds_min = [min(xs), min(ys), min(zs)]
            bounds_max = [max(xs), max(ys), max(zs)]
            bounds = [bounds_max[i] - bounds_min[i] for i in range(3)]
        else:
            bounds_min = [0.0, 0.0, 0.0]
            bounds_max = [0.0, 0.0, 0.0]
            bounds = [0.0, 0.0, 0.0]
        return {
            "vertices": vertices,
            "faces": faces,
            "bounds_min": bounds_min,
            "bounds_max": bounds_max,
            "bounds": bounds,
        }
    finally:
        evaluated.to_mesh_clear()


def _metric_delta(before, after, metric):
    if metric == "vertices":
        return abs(after["vertices"] - before["vertices"])
    return sum(abs(a - b) for a, b in zip(after["bounds"], before["bounds"]))


def _build_and_measure(tree_name, builder, params, suffix):
    mesh = bpy.data.meshes.new(f"Verify_{suffix}_Mesh")
    obj = bpy.data.objects.new(f"Verify_{suffix}", mesh)
    bpy.context.scene.collection.objects.link(obj)
    modifier = obj.modifiers.new(name="MelodiaHero", type="NODES")
    tree = builder(tree_name)
    missing = _set_modifier_inputs(modifier, tree, params)
    modifier.node_group = tree
    metrics = _evaluate(obj)
    return obj, tree, modifier, missing, metrics


def main():
    from surreal_arch.melodia_gn.core import GROUP_BUILDERS, GROUP_METADATA
    from surreal_arch.melodia_gn_route import ARCH_TO_GN
    from surreal_arch.quality_props import _DEFAULT_MELODIA_GN_ARCH_TYPES

    report = {
        "status": "pass",
        "blender": bpy.app.version_string,
        "integration": {},
        "targets": {},
    }
    failures = []

    route_targets = {
        "ESCHER_BELVEDERE": "MEL_escher_belvedere",
        "ESCHER_PENROSE_STAIRS": "MEL_escher_penrose_stairs",
        "ESCHER_WATERFALL": "MEL_escher_waterfall",
        "SKY_OBSERVATORY": "MEL_sky_observatory",
    }
    for arch_type, expected_tree in route_targets.items():
        route = ARCH_TO_GN.get(arch_type)
        report["integration"][arch_type] = {
            "route": route,
            "preferred": arch_type in _DEFAULT_MELODIA_GN_ARCH_TYPES,
        }
        if route is None or route[1] != expected_tree:
            failures.append(f"{arch_type}: ARCH_TO_GN route is missing or incorrect")
        if arch_type not in _DEFAULT_MELODIA_GN_ARCH_TYPES:
            failures.append(f"{arch_type}: Melodia GN preference allowlist is missing it")

    for tree_name, spec in TARGETS.items():
        entry = {
            "label": spec["label"],
            "builder_registered": tree_name in GROUP_BUILDERS,
            "metadata": {
                key: value
                for key, value in GROUP_METADATA.get(tree_name, {}).items()
                if key != "builder"
            },
            "probes": [],
        }
        report["targets"][tree_name] = entry
        if tree_name not in GROUP_BUILDERS:
            failures.append(f"{tree_name}: builder not registered")
            continue

        builder = GROUP_BUILDERS[tree_name]
        obj, tree, modifier, missing, baseline = _build_and_measure(
            tree_name, builder, spec["params"], tree_name.replace("MEL_", "baseline_")
        )
        entry["node_count"] = len(tree.nodes)
        entry["link_count"] = len(tree.links)
        entry["baseline"] = baseline
        entry["missing_baseline_inputs"] = missing
        if missing:
            failures.append(f"{tree_name}: missing baseline inputs {missing}")
        if baseline["vertices"] <= 0 or baseline["faces"] <= 0:
            failures.append(f"{tree_name}: empty evaluated geometry")
        if any(value <= 0.000001 for value in baseline["bounds"]):
            failures.append(f"{tree_name}: degenerate bounds {baseline['bounds']}")
        bpy.data.objects.remove(obj, do_unlink=True)

        for probe in spec["probes"]:
            probe_obj, probe_tree, probe_modifier, probe_missing, measured = _build_and_measure(
                tree_name,
                builder,
                {**spec["params"], **probe["params"]},
                f"{tree_name.replace('MEL_', '')}_{probe['name']}",
            )
            delta = _metric_delta(baseline, measured, probe["metric"])
            probe_result = {
                "name": probe["name"],
                "params": probe["params"],
                "metric": probe["metric"],
                "result": measured,
                "delta": delta,
                "missing_inputs": probe_missing,
            }
            entry["probes"].append(probe_result)
            if probe_missing:
                failures.append(f"{tree_name}/{probe['name']}: missing inputs {probe_missing}")
            if measured["vertices"] <= 0 or measured["faces"] <= 0:
                failures.append(f"{tree_name}/{probe['name']}: empty evaluated geometry")
            if delta <= 0.000001:
                failures.append(f"{tree_name}/{probe['name']}: parameter produced no measurable response")
            bpy.data.objects.remove(probe_obj, do_unlink=True)

    if failures:
        report["status"] = "fail"
        report["failures"] = failures
    else:
        report["failures"] = []

    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
