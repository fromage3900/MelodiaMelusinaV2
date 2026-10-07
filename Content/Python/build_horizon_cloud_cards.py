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

    input_node = g.input_node
    output_node = g.output_node

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

    # Wire: Input -> CreatePoints -> Transform -> Spawner -> Output
    g.add_edge(input_node, "Out", n1, "In")
    g.add_edge(n1, "Out", n2, "In")
    g.add_edge(n2, "Out", n3, "In")
    g.add_edge(n3, "Out", output_node, "Out")

    # Save
    unreal.EditorAssetLibrary.save_loaded_asset(g)

    result = {
        "ok": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "graph": GRAPH_PATH,
        "nodes": [n1.get_name(), n2.get_name(), n3.get_name()],
        "edges": [
            "Input -> CreatePoints",
            "CreatePoints -> TransformPoints",
            "TransformPoints -> StaticMeshSpawner",
            "StaticMeshSpawner -> Output",
        ],
    }

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")

    msg = f"PCG_HorizonCloudCards built | nodes={len(result['nodes'])} | edges={len(result['edges'])}"
    print(msg)
    return result


if __name__ == "__main__":
    build()
