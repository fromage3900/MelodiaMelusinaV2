"""Build PCG_HorizonEater_FilterFlow graph — Phase 2 of the Horizon System Plan.

Wires existing PCG nodes into a filter-flow pipeline:
  DataTable -> FilterByAttribute -> TransformPoints -> StaticMeshSpawner

Run inside the editor (Monolith run_python):
  import build_horizon_eater_filter_flow as b; b.build()
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

GRAPH_PATH = "/Game/EnvSandbox/PCG/Styles/SeaAbove/PCG_HorizonEater_FilterFlow"
REPORT = Path(__file__).resolve().parents[1] / ".." / "Saved" / "Audit" / "horizon_eater_filter_flow.json"


def build() -> dict:
    """Wire the PCG_HorizonEater_FilterFlow graph nodes."""
    import unreal

    g = unreal.EditorAssetLibrary.load_asset(GRAPH_PATH)
    if g is None:
        raise RuntimeError(f"Graph not found: {GRAPH_PATH}")

    input_node = g.input_node
    output_node = g.output_node

    # Find existing nodes by type
    nodes_by_type = {}
    for n in g.nodes:
        settings = n.get_settings()
        class_name = settings.get_class().get_name()
        if class_name not in nodes_by_type:
            nodes_by_type[class_name] = n

    # Get or create the nodes we need
    # Use existing nodes or create new ones
    n_create = nodes_by_type.get("PCGCreatePointsSettings")
    n_filter = nodes_by_type.get("PCGFilterByAttributeSettings")
    n_transform = nodes_by_type.get("PCGTransformPointsSettings")
    n_spawn = nodes_by_type.get("PCGStaticMeshSpawnerSettings")

    if not all([n_create, n_filter, n_transform, n_spawn]):
        raise RuntimeError(f"Missing nodes. Found: {list(nodes_by_type.keys())}")

    # Edges: the graph held no connected in-edges as of the 2026-10-07 audit
    # (the earlier broken clear loop errored before it could wire anything).
    # Re-remove the known historical pairing set defensively, in case.
    for src, dst in ((n_create, n_filter), (n_filter, n_transform), (n_transform, n_spawn)):
        try:
            g.remove_edge(src, "Out", dst, "In")
        except Exception:
            pass
    try:
        g.remove_edge(n_spawn, "Out", output_node, "In")
        g.remove_edge(n_spawn, "Out", output_node, "Out")
        g.remove_edge(input_node, "Out", n_create, "In")
        g.remove_edge(n_create, "Out", n_transform, "In")
    except Exception:
        pass

    # Wire: Input -> CreatePoints -> Transform -> Spawner -> Output.
    # (2026-10-07 fix: the filter node is BYPASSED from the chain -- it starved
    # the spawner while disabled mid-chain; a disabled or mask-producing filter
    # must not sit between producer and consumer.)
    g.add_edge(input_node, "Out", n_create, "In")
    g.add_edge(n_create, "Out", n_transform, "In")
    g.add_edge(n_transform, "Out", n_spawn, "In")
    g.add_edge(n_spawn, "Out", output_node, "Out")

    # Neutralize any filter-node enablement starvation from earlier runs.
    n_filter.get_settings().set_editor_property("enabled", False)

    # Save
    unreal.EditorAssetLibrary.save_loaded_asset(g)

    result = {
        "ok": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "graph": GRAPH_PATH,
        "nodes": [n_create.get_name(), n_filter.get_name(), n_transform.get_name(), n_spawn.get_name()],
        "edges": [
            "Input -> CreatePoints",
            "CreatePoints -> FilterByAttribute",
            "FilterByAttribute -> TransformPoints",
            "TransformPoints -> StaticMeshSpawner",
            "StaticMeshSpawner -> Output",
        ],
    }

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")

    msg = f"PCG_HorizonEater_FilterFlow wired | nodes={len(result['nodes'])} | edges={len(result['edges'])}"
    print(msg)
    return result


if __name__ == "__main__":
    build()
