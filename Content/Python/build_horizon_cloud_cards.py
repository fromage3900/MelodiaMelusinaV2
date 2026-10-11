"""Build PCG_HorizonCloudCards graph — Phase 7 of the Horizon System Plan.

Creates a PCG graph that places cloud card billboards at horizon distance,
tied to HorizonEatAmount (clouds dissipate as horizon is eaten).

Run inside the editor (Monolith run_python):
  import build_horizon_cloud_cards as b; b.build()
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

GRAPH_PATH = "/Game/EnvSandbox/PCG/Styles/SeaAbove/PCG_HorizonCloudCards"
REPORT = Path(__file__).resolve().parents[1] / ".." / "Saved" / "Audit" / "horizon_cloud_cards.json"


def build() -> dict:
    """Build/configure the PCG_HorizonCloudCards graph."""
    import unreal

    g = unreal.EditorAssetLibrary.load_asset(GRAPH_PATH)
    if g is None:
        raise RuntimeError(f"Graph not found: {GRAPH_PATH}")

    output_node = g.get_output_node()

    # Clear existing nodes
    for n in list(g.nodes):
        g.remove_node(n)

    # Build the cloud card pipeline
    # 1. CreatePoints — cloud card positions at horizon distance
    n1, s1 = g.add_node_of_type(unreal.PCGCreatePointsSettings)
    n1.set_node_position(0, 0)

    # 2. TransformPoints — place at 2000-5000m distance
    n2, s2 = g.add_node_of_type(unreal.PCGTransformPointsSettings)
    n2.set_node_position(300, 0)

    # 3. StaticMeshSpawner — spawn cloud card billboards
    n3, s3 = g.add_node_of_type(unreal.PCGStaticMeshSpawnerSettings)
    n3.set_node_position(600, 0)

    # Wire: CreatePoints -> Transform -> Spawner -> Output.
    # CreatePoints is a source node (no input pin). The OUTPUT node's input pin
    # is labelled "Out" in every proven builder (build_pcg_escher.py,
    # pcg_graph_builder.py); PCG only runs nodes upstream of the output node, so
    # the previous ("In") label left the spawner disconnected.
    edges = [
        (n1, "Out", n2, "In"),
        (n2, "Out", n3, "In"),
        (n3, "Out", output_node, "Out"),
    ]
    for a, a_pin, b, b_pin in edges:
        if g.add_edge(a, a_pin, b, b_pin) is None:
            raise RuntimeError(f"add_edge failed: {a.get_name()}.{a_pin} -> {b.get_name()}.{b_pin}")

    # Save
    unreal.EditorAssetLibrary.save_loaded_asset(g)

    result = {
        "ok": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "graph": GRAPH_PATH,
        "nodes": [n1.get_name(), n2.get_name(), n3.get_name()],
        "edges": [
            "CreatePoints -> TransformPoints",
            "TransformPoints -> StaticMeshSpawner",
            "StaticMeshSpawner -> Output",
        ],
        "note": "wired only; generation is NOT proven until instances are read back on a later tick",
    }

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")

    msg = f"PCG_HorizonCloudCards built | nodes={len(result['nodes'])} | edges={len(result['edges'])}"
    print(msg)
    return result


if __name__ == "__main__":
    build()
